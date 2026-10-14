"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/app/components/Sidebar";
import { api, getToken, puedeAlguno } from "@/app/lib/api";
import { usePerfil } from "@/app/lib/use-perfil";
import { Badge } from "@/app/components/ui/badge";
import { Card, CardContent } from "@/app/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/app/components/ui/table";

interface Curso {
  id: string;
  nombre: string;
  anio_inicio: number | null;
  anio_fin: number | null;
  activo: boolean;
  es_curso_actual: boolean;
}

export default function CursosPage() {
  const [cursos, setCursos] = useState<Curso[]>([]);
  const { cargado } = usePerfil();

  useEffect(() => {
    if (!getToken()) {
      window.location.href = "/login";
      return;
    }
    void (async () => {
      setCursos(await api<Curso[]>("/catalogos/cursos"));
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
        <h1 className="text-xl font-bold mb-4">Cursos academicos</h1>
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>NOMBRE</TableHead>
                  <TableHead>INICIO</TableHead>
                  <TableHead>FIN</TableHead>
                  <TableHead>CURSO ACTUAL</TableHead>
                  <TableHead>ESTADO</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {cursos.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell className="font-semibold text-cujae">{c.nombre}</TableCell>
                    <TableCell>{c.anio_inicio ?? "-"}</TableCell>
                    <TableCell>{c.anio_fin ?? "-"}</TableCell>
                    <TableCell>
                      {c.es_curso_actual ? (
                        <Badge variant="success">Actual</Badge>
                      ) : (
                        "-"
                      )}
                    </TableCell>
                    <TableCell>
                      {c.activo ? (
                        <Badge variant="success">Activo</Badge>
                      ) : (
                        <Badge variant="secondary">Inactivo</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
                {cursos.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="py-8 text-center text-muted-foreground">
                      Sin cursos registrados
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
