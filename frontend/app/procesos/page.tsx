"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/app/components/Sidebar";
import { api, getToken, puedeAlguno, TIPO_BADGE } from "@/app/lib/api";
import { usePerfil } from "@/app/lib/use-perfil";
import { Badge } from "@/app/components/ui/badge";
import { Card, CardContent } from "@/app/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/app/components/ui/table";

interface Proceso {
  id: string;
  codigo: string;
  nombre: string;
  tipo: string;
  descripcion: string | null;
  activo: boolean;
}

export default function ProcesosPage() {
  const [procesos, setProcesos] = useState<Proceso[]>([]);
  const { cargado } = usePerfil();

  useEffect(() => {
    if (!getToken()) {
      window.location.href = "/login";
      return;
    }
    void (async () => {
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
        <h1 className="text-xl font-bold mb-4">Procesos institucionales</h1>
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>CODIGO</TableHead>
                  <TableHead>NOMBRE</TableHead>
                  <TableHead>TIPO</TableHead>
                  <TableHead>DESCRIPCION</TableHead>
                  <TableHead>ESTADO</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {procesos.map((p) => (
                  <TableRow key={p.id}>
                    <TableCell className="font-semibold text-cujae">{p.codigo}</TableCell>
                    <TableCell>{p.nombre}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className={TIPO_BADGE[p.tipo]}>
                        {p.tipo}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground max-w-md truncate">{p.descripcion ?? "-"}</TableCell>
                    <TableCell>
                      {p.activo ? (
                        <Badge variant="success">Activo</Badge>
                      ) : (
                        <Badge variant="secondary">Inactivo</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
                {procesos.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="py-8 text-center text-muted-foreground">
                      Sin procesos registrados
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
