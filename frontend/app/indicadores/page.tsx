"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Sidebar from "@/app/components/Sidebar";
import { api, getToken, puede, TIPO_BADGE, type Indicador } from "@/app/lib/api";
import { usePerfil } from "@/app/lib/use-perfil";
import { Badge } from "@/app/components/ui/badge";
import { Card, CardContent } from "@/app/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/app/components/ui/table";

interface Proceso {
  id: string;
  nombre: string;
  tipo: string;
}

export default function IndicadoresPage() {
  const [indicadores, setIndicadores] = useState<Indicador[]>([]);
  const [procesos, setProcesos] = useState<Proceso[]>([]);
  const { cargado } = usePerfil();

  useEffect(() => {
    if (!getToken()) {
      window.location.href = "/login";
      return;
    }
    if (!puede("indicadores")) return;
    void (async () => {
      setIndicadores(await api<Indicador[]>("/indicadores"));
      setProcesos(await api<Proceso[]>("/catalogos/procesos"));
    })();
  }, []);

  if (!cargado) return null;

  if (!puede("indicadores")) {
    return (
      <div className="min-h-screen">
        <Sidebar />
        <div className="ml-64 p-6">
          <Card className="text-center py-10 text-muted-foreground">
            Tu rol no tiene acceso a los indicadores (RF-04).
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Sidebar />
      <div className="ml-64 p-6">
        <h1 className="text-xl font-bold mb-4">Indicadores de gestion</h1>
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>CODIGO</TableHead>
                  <TableHead>NOMBRE</TableHead>
                  <TableHead>TIPO</TableHead>
                  <TableHead>ESTADO</TableHead>
                  <TableHead>ACCIONES</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {indicadores.map((i) => {
                  const p = procesos.find((pr) => pr.id === i.proceso_id);
                  return (
                    <TableRow key={i.id}>
                      <TableCell className="font-semibold text-cujae">{i.codigo}</TableCell>
                      <TableCell>{i.nombre}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={TIPO_BADGE[p?.tipo ?? ""]}>
                          {p?.tipo ?? "-"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {i.activo ? (
                          <Badge variant="success">Activo</Badge>
                        ) : (
                          <Badge variant="secondary">Inactivo</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <Link href={`/indicadores/${i.id}`} className="text-cujae hover:underline">
                          Ver detalle
                        </Link>
                      </TableCell>
                    </TableRow>
                  );
                })}
                {indicadores.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="py-8 text-center text-muted-foreground">
                      Sin indicadores registrados
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
