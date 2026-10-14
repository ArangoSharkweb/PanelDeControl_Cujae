"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/app/components/Sidebar";
import { api, getToken, puedeAlguno } from "@/app/lib/api";
import { usePerfil } from "@/app/lib/use-perfil";
import { Badge } from "@/app/components/ui/badge";
import { Card, CardContent } from "@/app/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/app/components/ui/table";

interface Unidad {
  id: string;
  codigo: string;
  nombre: string;
  tipo: string | null;
  responsable_id: string | null;
  activo: boolean;
}

export default function UnidadesPage() {
  const [unidades, setUnidades] = useState<Unidad[]>([]);
  const { cargado } = usePerfil();

  useEffect(() => {
    if (!getToken()) {
      window.location.href = "/login";
      return;
    }
    void (async () => {
      setUnidades(await api<Unidad[]>("/catalogos/unidades"));
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
        <h1 className="text-xl font-bold mb-4">Unidades organizativas</h1>
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>CODIGO</TableHead>
                  <TableHead>NOMBRE</TableHead>
                  <TableHead>TIPO</TableHead>
                  <TableHead>ESTADO</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {unidades.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell className="font-semibold text-cujae">{u.codigo}</TableCell>
                    <TableCell>{u.nombre}</TableCell>
                    <TableCell>{u.tipo ?? "-"}</TableCell>
                    <TableCell>
                      {u.activo ? (
                        <Badge variant="success">Activa</Badge>
                      ) : (
                        <Badge variant="secondary">Inactiva</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
                {unidades.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} className="py-8 text-center text-muted-foreground">
                      Sin unidades registradas
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
