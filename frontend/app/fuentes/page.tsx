"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/app/components/Sidebar";
import { api, getToken, puede } from "@/app/lib/api";
import { usePerfil } from "@/app/lib/use-perfil";
import { Badge } from "@/app/components/ui/badge";
import { Button } from "@/app/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Input } from "@/app/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/app/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/app/components/ui/table";

interface Fuente {
  id: string;
  codigo: string;
  nombre: string;
  tipo: string;
  motor: string | null;
  host: string | null;
  puerto: number | null;
  database: string | null;
  activo: boolean;
  solo_lectura: boolean;
  ultima_prueba: string | null;
  estado_prueba: string | null;
}

interface Descubrimiento {
  fuente_id: string;
  tablas: Record<string, unknown>[];
  errores: string[];
}

const TIPOS = ["postgresql", "sqlserver", "excel"];

export default function FuentesPage() {
  const [fuentes, setFuentes] = useState<Fuente[]>([]);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [descubrimiento, setDescubrimiento] = useState<Descubrimiento | null>(null);
  const [probarId, setProbarId] = useState<string | null>(null);
  const [mostrarForm, setMostrarForm] = useState(false);
  const { cargado } = usePerfil();
  const [nueva, setNueva] = useState({
    codigo: "",
    nombre: "",
    tipo: "postgresql",
    host: "",
    puerto: "5432",
    database: "",
    usuario: "",
    password: "",
  });

  const cargar = async () => {
    setFuentes(await api<Fuente[]>("/fuentes"));
  };

  useEffect(() => {
    if (!getToken()) {
      window.location.href = "/login";
      return;
    }
    if (!puede("fuentes")) return;
    void cargar().catch(() => setMensaje("No se pudieron cargar las fuentes"));
  }, []);

  const crearFuente = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api("/fuentes", {
        method: "POST",
        body: JSON.stringify({
          codigo: nueva.codigo,
          nombre: nueva.nombre,
          tipo: nueva.tipo,
          host: nueva.host || null,
          puerto: nueva.puerto ? Number(nueva.puerto) : null,
          database: nueva.database || null,
          usuario: nueva.usuario || null,
          password: nueva.password || null,
        }),
      });
      setMensaje(`Fuente "${nueva.nombre}" creada`);
      setMostrarForm(false);
      setNueva({ codigo: "", nombre: "", tipo: "postgresql", host: "", puerto: "5432", database: "", usuario: "", password: "" });
      await cargar();
    } catch (err) {
      setMensaje(err instanceof Error ? err.message : "Error al crear la fuente");
    }
  };

  const probar = async (f: Fuente) => {
    setProbarId(f.id);
    setDescubrimiento(null);
    setMensaje(null);
    try {
      const res = await api<Descubrimiento>(`/fuentes/${f.id}/probar`, { method: "POST" });
      setDescubrimiento(res);
      await cargar();
    } catch (err) {
      setMensaje(err instanceof Error ? err.message : "Error al probar la fuente");
    } finally {
      setProbarId(null);
    }
  };

  if (!cargado) return null;

  if (!puede("fuentes")) {
    return (
      <div className="min-h-screen">
        <Sidebar />
        <div className="ml-64 p-6">
          <Card className="text-center py-10 text-muted-foreground">
            Tu rol no tiene acceso a las fuentes de datos (RF-04).
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
          <h1 className="text-xl font-bold">Fuentes de datos disponibles</h1>
          <Button onClick={() => setMostrarForm((v) => !v)}>
            {mostrarForm ? "Cancelar" : "+ Nueva fuente"}
          </Button>
        </div>
        <p className="text-sm text-muted-foreground">
          Conexiones institucionales de solo lectura de las que se toman los datos para el calculo
          (RNF-09: las credenciales nunca se muestran).
        </p>

        {mensaje && (
          <div className="bg-accent text-accent-foreground text-sm rounded-lg px-3 py-2">{mensaje}</div>
        )}

        {descubrimiento && (
          <Card className="text-sm">
            <div className="font-semibold">Resultado de la prueba de conexion</div>
            {descubrimiento.errores.length > 0 ? (
              <ul className="text-destructive list-disc pl-4 mt-1">
                {descubrimiento.errores.map((e) => (
                  <li key={e}>{e}</li>
                ))}
              </ul>
            ) : (
              <div className="text-emerald-600 mt-1">
                Conexion OK · {descubrimiento.tablas.length} tabla(s) descubierta(s)
                {descubrimiento.tablas.length > 0 && (
                  <span className="text-muted-foreground">
                    {" "}
                    · {descubrimiento.tablas.map((t) => String(t.nombre ?? t.table ?? "?")).join(", ")}
                  </span>
                )}
              </div>
            )}
          </Card>
        )}

        {mostrarForm && (
          <Card>
            <CardContent className="pt-6">
              <form onSubmit={crearFuente} className="grid grid-cols-1 md:grid-cols-4 gap-3">
                <Input
                  placeholder="Codigo *"
                  value={nueva.codigo}
                  onChange={(e) => setNueva({ ...nueva, codigo: e.target.value })}
                  required
                />
                <Input
                  placeholder="Nombre *"
                  value={nueva.nombre}
                  onChange={(e) => setNueva({ ...nueva, nombre: e.target.value })}
                  required
                />
                <Select value={nueva.tipo} onValueChange={(v) => setNueva({ ...nueva, tipo: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TIPOS.map((t) => (
                      <SelectItem key={t} value={t}>
                        {t}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Input
                  placeholder="Host"
                  value={nueva.host}
                  onChange={(e) => setNueva({ ...nueva, host: e.target.value })}
                />
                <Input
                  placeholder="Puerto"
                  value={nueva.puerto}
                  onChange={(e) => setNueva({ ...nueva, puerto: e.target.value })}
                />
                <Input
                  placeholder="Base de datos"
                  value={nueva.database}
                  onChange={(e) => setNueva({ ...nueva, database: e.target.value })}
                />
                <Input
                  placeholder="Usuario"
                  value={nueva.usuario}
                  onChange={(e) => setNueva({ ...nueva, usuario: e.target.value })}
                />
                <Input
                  type="password"
                  placeholder="Password (se cifra)"
                  value={nueva.password}
                  onChange={(e) => setNueva({ ...nueva, password: e.target.value })}
                />
                <Button type="submit" className="md:col-span-2">
                  Crear fuente
                </Button>
              </form>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>CODIGO</TableHead>
                  <TableHead>NOMBRE</TableHead>
                  <TableHead>TIPO</TableHead>
                  <TableHead>CONEXION</TableHead>
                  <TableHead>ESTADO PRUEBA</TableHead>
                  <TableHead>ULTIMA PRUEBA</TableHead>
                  <TableHead>ACCIONES</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {fuentes.map((f) => (
                  <TableRow key={f.id}>
                    <TableCell className="font-semibold text-cujae">{f.codigo}</TableCell>
                    <TableCell>{f.nombre}</TableCell>
                    <TableCell>
                      <Badge variant="info">{f.tipo}</Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {f.host ? `${f.host}:${f.puerto ?? "-"}/${f.database ?? "-"}` : "archivo"}
                      {f.solo_lectura && (
                        <Badge variant="secondary" className="ml-2">
                          solo lectura
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {f.estado_prueba === "ok" ? (
                        <span className="text-emerald-600">OK</span>
                      ) : f.estado_prueba === "error" ? (
                        <span className="text-destructive">Error</span>
                      ) : (
                        <span className="text-muted-foreground/60">Sin probar</span>
                      )}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {f.ultima_prueba ? new Date(f.ultima_prueba).toLocaleString("es-CU") : "-"}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="link"
                        size="sm"
                        className="h-auto p-0"
                        disabled={probarId === f.id || !f.activo}
                        onClick={() => void probar(f)}
                      >
                        {probarId === f.id ? "Probando..." : "Probar"}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {fuentes.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} className="py-8 text-center text-muted-foreground">
                      Sin fuentes configuradas
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
