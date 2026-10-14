"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/app/components/Sidebar";
import { api, getToken, puedeAlguno } from "@/app/lib/api";
import { usePerfil } from "@/app/lib/use-perfil";
import { Badge } from "@/app/components/ui/badge";
import { Card, CardContent } from "@/app/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/app/components/ui/table";

interface Objetivo {
  id: string;
  codigo: string;
  nombre: string;
  descripcion: string | null;
  proceso_id: string | null;
  activo: boolean;
}

interface Proceso {
  id: string;
  nombre: string;
}

export default function ObjetivosPage() {
  const [objetivos, setObjetivos] = useState<Objetivo[]>([]);
  const [procesos, setProcesos] = useState<Proceso[]>([]);
  const { cargado } = usePerfil();

  useEffect(() => {
    if (!getToken()) {
      window.location.href = "/login";
      return;
    }
    void (async () => {
      setObjetivos(await api<Objetivo[]>("/catalogos/objetivos"));
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
        <h1 className="text-xl font-bold mb-4">Objetivos estrategicos</h1>
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>CODIGO</TableHead>
                  <TableHead>NOMBRE</TableHead>
                  <TableHead>PROCESO</TableHead>
                  <TableHead>DESCRIPCION</TableHead>
                  <TableHead>ESTADO</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {objetivos.map((o) => {
                  const p = procesos.find((pr) => pr.id === o.proceso_id);
                  return (
                    <TableRow key={o.id}>
                      <TableCell className="font-semibold text-cujae">{o.codigo}</TableCell>
                      <TableCell>{o.nombre}</TableCell>
                      <TableCell>{p?.nombre ?? "-"}</TableCell>
                      <TableCell className="text-muted-foreground max-w-md truncate">{o.descripcion ?? "-"}</TableCell>
                      <TableCell>
                        {o.activo ? (
                          <Badge variant="success">Activo</Badge>
                        ) : (
                          <Badge variant="secondary">Inactivo</Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
                {objetivos.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="py-8 text-center text-muted-foreground">
                      Sin objetivos registrados
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
