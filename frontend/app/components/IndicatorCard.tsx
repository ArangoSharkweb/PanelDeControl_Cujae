"use client";

import Link from "next/link";
import { SEMAFORO_COLOR, TIPO_BADGE, type Indicador, type Valor } from "@/app/lib/api";
import { Badge } from "@/app/components/ui/badge";
import { Card, CardContent } from "@/app/components/ui/card";

interface Props {
  indicador: Indicador;
  valor: Valor | null;
  meta: string;
  curso: string;
  procesoNombre: string;
  procesoTipo: string;
}

export default function IndicatorCard({ indicador, valor, meta, curso, procesoNombre, procesoTipo }: Props) {
  const estado = valor?.estado_semaforo ?? "verde";

  return (
    <Card className="flex flex-col gap-3">
      <CardContent className="p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs font-bold text-cujae">{indicador.codigo}</div>
          <div className="font-semibold leading-tight">{indicador.nombre}</div>
        </div>
        <Badge variant="outline" className={TIPO_BADGE[procesoTipo]}>
          {procesoNombre}
        </Badge>
      </div>

      <div className="flex items-end gap-3">
        <div
          className="text-4xl font-bold"
          style={{ color: SEMAFORO_COLOR[estado] }}
        >
          {valor?.valor ?? "--"}
        </div>
        <div className="text-sm text-muted-foreground pb-1">
          <div>Meta: {meta}</div>
          <div>
            {curso} ·{" "}
            {valor?.calculado_en
              ? new Date(valor.calculado_en).toLocaleDateString()
              : "sin calculo"}
          </div>
        </div>
      </div>

      <div className="h-2 rounded-full bg-muted overflow-hidden">
        <div
          className="h-full"
          style={{
            width: `${Math.min(Number(valor?.porcentaje_meta ?? 0), 100)}%`,
            backgroundColor: SEMAFORO_COLOR[estado],
          }}
        />
      </div>

      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <Link href={`/indicadores/${indicador.id}`} className="text-cujae hover:underline">
          Ver detalle
        </Link>
      </div>
      </CardContent>
    </Card>
  );
}
