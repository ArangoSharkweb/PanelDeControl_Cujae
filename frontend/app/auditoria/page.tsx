"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import Sidebar from "@/app/components/Sidebar";
import { api, getToken, puede, type SecurityLog } from "@/app/lib/api";
import { usePerfil } from "@/app/lib/use-perfil";
import { Badge } from "@/app/components/ui/badge";
import { Button } from "@/app/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Input } from "@/app/components/ui/input";
import { Label } from "@/app/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/app/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/app/components/ui/table";

const EVENTOS = [
  "",
  "login",
  "failed_login",
  "indicator_create",
  "indicator_modify",
  "indicator_delete",
  "user_create",
  "user_modify",
  "config_change",
  "recalc_trigger",
  "data_export",
];

const COLOR_SEV: Record<string, string> = {
  INFO: "#16a34a",
  WARNING: "#f59e0b",
  CRITICAL: "#dc2626",
};

export default function AuditoriaPage() {
  const [logs, setLogs] = useState<SecurityLog[]>([]);
  const [evento, setEvento] = useState("");
  const [severidad, setSeveridad] = useState("");
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");

  const cargar = useCallback(async () => {
    const params = new URLSearchParams();
    if (evento) params.set("event_type", evento);
    if (severidad) params.set("severidad", severidad);
    if (desde) params.set("desde", new Date(desde).toISOString());
    if (hasta) params.set("hasta", new Date(hasta).toISOString());
    params.set("limite", "300");
    setLogs(await api<SecurityLog[]>(`/logs/security?${params.toString()}`));
  }, [evento, severidad, desde, hasta]);

  const { cargado } = usePerfil();

  useEffect(() => {
    if (!getToken()) {
      window.location.href = "/login";
      return;
    }
    if (!puede("auditoria")) return;
    void cargar();
  }, [cargar]);

  const exportar = async (formato: "json" | "csv") => {
    const token = getToken();
    const params = new URLSearchParams({ formato });
    if (desde) params.set("desde", new Date(desde).toISOString());
    if (hasta) params.set("hasta", new Date(hasta).toISOString());
    const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
    const res = await fetch(`${base}/logs/export?${params}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `security_logs.${formato}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const eventosChart = useMemo(() => {
    const counts: Record<string, number> = {};
    logs.forEach((l) => {
      counts[l.event_type] = (counts[l.event_type] ?? 0) + 1;
    });
    return Object.entries(counts).map(([name, cantidad]) => ({ name, cantidad }));
  }, [logs]);

  const heatmap = useMemo(() => {
    const dias = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sat", "Dom"];
    const grid = dias.map((d) => ({ dia: d, horas: Array.from({ length: 24 }, () => 0) }));
    logs.forEach((l) => {
      const fecha = new Date(l.ts);
      const idx = (fecha.getDay() + 6) % 7;
      grid[idx].horas[fecha.getHours()] += 1;
    });
    return grid;
  }, [logs]);

  const maxHora = Math.max(1, ...heatmap.flatMap((g) => g.horas));

  if (!cargado) return null;

  if (!puede("auditoria")) {
    return (
      <div className="min-h-screen">
        <Sidebar />
        <div className="ml-64 p-6">
          <Card className="text-center py-10 text-muted-foreground">
            Tu rol no tiene acceso a la auditoria del sistema (RF-04).
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Sidebar />
      <div className="ml-64 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold">Auditoria del sistema</h1>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => void exportar("json")}>
              Exportar JSON
            </Button>
            <Button variant="outline" size="sm" onClick={() => void exportar("csv")}>
              Exportar CSV
            </Button>
          </div>
        </div>

        <Card>
          <CardContent className="pt-6 flex flex-wrap gap-3 items-end">
            <div className="space-y-1">
              <Label className="text-xs text-muted-foreground">Evento</Label>
              <Select value={evento || "todos"} onValueChange={(v) => setEvento(v === "todos" ? "" : v)}>
                <SelectTrigger className="w-48 h-9">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {EVENTOS.map((e) => (
                    <SelectItem key={e || "todos"} value={e || "todos"}>
                      {e || "Todos"}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label className="text-xs text-muted-foreground">Severidad</Label>
              <Select value={severidad || "todas"} onValueChange={(v) => setSeveridad(v === "todas" ? "" : v)}>
                <SelectTrigger className="w-40 h-9">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todas">Todas</SelectItem>
                  <SelectItem value="INFO">INFO</SelectItem>
                  <SelectItem value="WARNING">WARNING</SelectItem>
                  <SelectItem value="CRITICAL">CRITICAL</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label className="text-xs text-muted-foreground">Desde</Label>
              <Input type="date" value={desde} onChange={(e) => setDesde(e.target.value)} className="h-9 w-40" />
            </div>
            <div className="space-y-1">
              <Label className="text-xs text-muted-foreground">Hasta</Label>
              <Input type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} className="h-9 w-40" />
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Eventos por tipo</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={eventosChart}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" fontSize={9} />
                  <YAxis fontSize={11} />
                  <Tooltip />
                  <Bar dataKey="cantidad" fill="#16a34a" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Mapa de calor de accesos (hora/dia)</CardTitle>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="text-[10px] border-collapse">
                <tbody>
                  {heatmap.map((fila) => (
                    <tr key={fila.dia}>
                      <td className="pr-2 text-muted-foreground">{fila.dia}</td>
                      {fila.horas.map((h, i) => (
                        <td
                          key={i}
                          title={`${fila.dia} ${i}:00 -> ${h} eventos`}
                          className="w-5 h-5 border"
                          style={{
                            backgroundColor: `rgba(22,163,74,${(h / maxHora) * 0.9})`,
                          }}
                        />
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>TIMESTAMP</TableHead>
                  <TableHead>USUARIO</TableHead>
                  <TableHead>EVENTO</TableHead>
                  <TableHead>SEVERIDAD</TableHead>
                  <TableHead>RECURSO</TableHead>
                  <TableHead>ACCION</TableHead>
                  <TableHead>DETALLE</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((l) => (
                  <TableRow key={l.log_id}>
                    <TableCell>{new Date(l.ts).toLocaleString()}</TableCell>
                    <TableCell>{l.usuario.username ?? "-"}</TableCell>
                    <TableCell>{l.event_type}</TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        style={{
                          backgroundColor: `${COLOR_SEV[l.severity]}22`,
                          color: COLOR_SEV[l.severity],
                        }}
                      >
                        {l.severity}
                      </Badge>
                    </TableCell>
                    <TableCell>{l.action.resource_type ?? "-"}</TableCell>
                    <TableCell>{l.action.operation ?? "-"}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{l.session.ip_address ?? "-"}</TableCell>
                  </TableRow>
                ))}
                {logs.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} className="py-8 text-center text-muted-foreground">
                      Sin eventos para los filtros seleccionados
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
