"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/app/components/ui/card";

const COLORES: Record<string, string> = {
  verde: "#16a34a",
  amarillo: "#f59e0b",
  rojo: "#dc2626",
};

export function EstadoGeneral({ datos }: { datos: { estado: string; cantidad: number }[] }) {
  const total = datos.reduce((acc, d) => acc + d.cantidad, 0);
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Estado general</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
      <div className="h-44">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={datos}
              dataKey="cantidad"
              nameKey="estado"
              innerRadius={45}
              outerRadius={70}
              paddingAngle={2}
            >
              {datos.map((d) => (
                <Cell key={d.estado} fill={COLORES[d.estado] ?? "#94a3b8"} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="flex justify-around text-xs">
        {datos.map((d) => (
          <span key={d.estado} className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: COLORES[d.estado] }} />
            {d.estado} ({d.cantidad}/{total})
          </span>
        ))}
      </div>
      </CardContent>
    </Card>
  );
}

export function GaugeEsenciales({ porcentaje }: { porcentaje: number }) {
  const color = porcentaje >= 90 ? "#16a34a" : porcentaje >= 70 ? "#f59e0b" : "#dc2626";
  const radio = 70;
  const circunferencia = Math.PI * radio;
  const avance = (porcentaje / 100) * circunferencia;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Indicadores esenciales</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
      <svg viewBox="0 0 160 95" className="w-full h-40">
        <path
          d="M 15 85 A 65 65 0 0 1 145 85"
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="14"
          strokeLinecap="round"
        />
        <path
          d="M 15 85 A 65 65 0 0 1 145 85"
          fill="none"
          stroke={color}
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray={`${(porcentaje / 100) * 204} 204`}
        />
        <text x="80" y="78" textAnchor="middle" className="fill-foreground" fontSize="24" fontWeight="700">
          {porcentaje}%
        </text>
      </svg>
      <p className="text-xs text-muted-foreground text-center">KPIs esenciales cumplidos</p>
      </CardContent>
    </Card>
  );
}
