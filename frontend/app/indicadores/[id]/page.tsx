"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import Sidebar from "@/app/components/Sidebar";
import {
  api,
  getToken,
  puede,
  SEMAFORO_COLOR,
  type Indicador,
  type Valor,
} from "@/app/lib/api";
import { usePerfil } from "@/app/lib/use-perfil";
import { Card, CardContent, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Skeleton } from "@/app/components/ui/skeleton";

export default function IndicadorDetalle() {
  const params = useParams<{ id: string }>();
  const [indicador, setIndicador] = useState<Indicador | null>(null);
  const [valores, setValores] = useState<Valor[]>([]);
  const { cargado } = usePerfil();

  useEffect(() => {
    if (!getToken()) {
      window.location.href = "/login";
      return;
    }
    if (!puede("indicadores")) return;
    if (!params.id) return;
    void (async () => {
      setIndicador(await api<Indicador>(`/indicadores/${params.id}`));
      setValores(
        (await api<Valor[]>(`/indicadores/${params.id}/valores`)).filter((v) => v.valor !== null)
      );
    })();
  }, [params.id]);

  if (!cargado) {
    return (
      <div className="min-h-screen">
        <Sidebar />
        <div className="ml-64 p-6 space-y-4">
          <Skeleton className="h-10 w-72" />
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
          </div>
          <Skeleton className="h-72" />
        </div>
      </div>
    );
  }

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

  const serie = valores
    .slice()
    .reverse()
    .map((v) => ({
      fecha: v.calculado_en ? new Date(v.calculado_en).toLocaleDateString() : "",
      valor: Number(v.valor ?? 0),
      meta: Number(indicador?.metas?.[0]?.valor_meta ?? 0),
      estado: v.estado_semaforo ?? "verde",
    }));

  const ultimo = valores[0];

  return (
    <div className="min-h-screen">
      <Sidebar />
      <div className="ml-64 p-6 space-y-4">
        {indicador && (
          <>
            <div className="flex items-start justify-between">
              <div>
                <div className="text-cujae font-bold">{indicador.codigo}</div>
                <h1 className="text-xl font-bold">{indicador.nombre}</h1>
                <p className="text-sm text-muted-foreground max-w-2xl">{indicador.descripcion}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="text-xs text-muted-foreground">Valor actual</div>
                  <div
                    className="text-3xl font-bold"
                    style={{ color: SEMAFORO_COLOR[ultimo?.estado_semaforo ?? "verde"] }}
                  >
                    {ultimo?.valor ?? "--"}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-xs text-muted-foreground">Meta anual</div>
                  <div className="text-3xl font-bold">{indicador.metas?.[0]?.valor_meta ?? "--"}</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-xs text-muted-foreground">Cumplimiento</div>
                  <div className="text-3xl font-bold">{ultimo?.porcentaje_meta ?? "--"}%</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-xs text-muted-foreground">Estado</div>
                  <div
                    className="text-3xl font-bold capitalize"
                    style={{ color: SEMAFORO_COLOR[ultimo?.estado_semaforo ?? "verde"] }}
                  >
                    {ultimo?.estado_semaforo ?? "--"}
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card className="h-72">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Evolucion vs meta</CardTitle>
              </CardHeader>
              <CardContent className="h-[calc(100%-3rem)]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={serie}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="fecha" fontSize={11} />
                    <YAxis fontSize={11} />
                    <Tooltip />
                    <Line type="monotone" dataKey="valor" stroke="#16a34a" strokeWidth={2} />
                    <Line type="monotone" dataKey="meta" stroke="#94a3b8" strokeDasharray="5 5" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Formula y variables</CardTitle>
              </CardHeader>
              <CardContent>
                <code className="block bg-muted rounded p-2 text-sm mb-2">
                  {indicador.formula ?? "Sin formula configurada"}
                </code>
                <ul className="text-sm list-disc pl-5">
                  {(indicador.variables ?? []).map((v) => (
                    <li key={v.id}>
                      {v.nombre} = {v.funcion_agregacion ?? "-"}({v.columna ?? "-"}) de{" "}
                      {v.tabla ?? "-"}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
