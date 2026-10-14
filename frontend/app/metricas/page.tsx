"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/app/components/Sidebar";
import { api, getToken, puedeAlguno, TIPO_BADGE } from "@/app/lib/api";
import { usePerfil } from "@/app/lib/use-perfil";
import { Badge } from "@/app/components/ui/badge";
import { Card, CardContent } from "@/app/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/app/components/ui/table";

interface Metrica {
  id: string;
  codigo: string;
  nombre: string;
  proceso_id: string | null;
}

interface Proceso {
  id: string;
  nombre: string;
  tipo: string;
}

export default function MetricasPage() {
  const [metricas, setMetricas] = useState<Metrica[]>([]);
  const [procesos, setProcesos] = useState<Proceso[]>([]);
  const { cargado } = usePerfil();

  useEffect(() => {
    if (!getToken()) {
      window.location.href = "/login";
      return;
    }
    void (async () => {
      setMetricas(await api<Metrica[]>("/catalogos/metricas"));
      setProcesos(await api<Proceso[]>("/catalogos/procesos"));
    })();
  }, []);

  if (!cargado) return null;

  if (!puedeAlguno(["tablero", "indicadores"])) {
    return (
      <div className="min-h-screen">
        <Sidebar />
        <div className="ml-64 p-6">
          <Card className="text-center py-10 text-muted-foreground">
            Tu rol no tiene acceso a este catalogo (RF-04).
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Sidebar />
      <div className="ml-64 p-6">
        <h1 className="text-xl font-bold mb-4">Metricas por proceso</h1>
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>CODIGO</TableHead>
                  <TableHead>NOMBRE</TableHead>
                  <TableHead>PROCESO</TableHead>
                  <TableHead>TIPO PROCESO</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {metricas.map((m) => {
                  const p = procesos.find((pr) => pr.id === m.proceso_id);
                  return (
                    <TableRow key={m.id}>
                      <TableCell className="font-semibold text-cujae">{m.codigo}</TableCell>
                      <TableCell>{m.nombre}</TableCell>
                      <TableCell>{p?.nombre ?? "-"}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={TIPO_BADGE[p?.tipo ?? ""]}>
                          {p?.tipo ?? "-"}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  );
                })}
                {metricas.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} className="py-8 text-center text-muted-foreground">
                      Sin metricas registradas
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
