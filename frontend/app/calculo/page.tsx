"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/app/components/Sidebar";
import { api, getToken, puede } from "@/app/lib/api";
import { usePerfil } from "@/app/lib/use-perfil";
import { Badge } from "@/app/components/ui/badge";
import { Button } from "@/app/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Input } from "@/app/components/ui/input";
import { Label } from "@/app/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/app/components/ui/radio-group";

interface EstadoCalculo {
  frecuencia: string;
  intervalo_horas: number | null;
  hora_diaria: string | null;
  proxima_ejecucion: string | null;
}

interface ResultadoRecalculo {
  calculados: number;
  errores: number;
  detalles: string[];
}

const INTERVALOS = [1, 3, 6, 12, 24];

export default function CalculoPage() {
  const [estado, setEstado] = useState<EstadoCalculo | null>(null);
  const [modo, setModo] = useState<"intervalo" | "diario">("intervalo");
  const [intervalo, setIntervalo] = useState(6);
  const [hora, setHora] = useState("02:00");
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [resultado, setResultado] = useState<ResultadoRecalculo | null>(null);
  const [calculando, setCalculando] = useState(false);
  const { cargado } = usePerfil();

  const cargar = async () => {
    const e = await api<EstadoCalculo>("/config/estado-calculo");
    setEstado(e);
    if (e.intervalo_horas) {
      setModo("intervalo");
      setIntervalo(e.intervalo_horas);
    } else {
      setModo("diario");
      if (e.hora_diaria) setHora(e.hora_diaria);
    }
  };

  useEffect(() => {
    if (!getToken()) {
      window.location.href = "/login";
      return;
    }
    if (!puede("config")) return;
    void cargar().catch(() => setMensaje("No se pudo leer la programacion actual"));
  }, []);

  const guardar = async () => {
    try {
      if (modo === "intervalo") {
        await api("/config/intervalo_recalculo_horas", {
          method: "PUT",
          body: JSON.stringify({
            clave: "intervalo_recalculo_horas",
            valor: String(intervalo),
            descripcion: "Cada cuantos horas se ejecuta el recalculo de indicadores",
          }),
        });
        setMensaje(`Calculo programado: cada ${intervalo} horas`);
      } else {
        await api("/config/hora_recalculo", {
          method: "PUT",
          body: JSON.stringify({
            clave: "hora_recalculo",
            valor: hora,
            descripcion: "Hora diaria de recalculo de indicadores",
          }),
        });
        setMensaje(`Calculo programado: diario a las ${hora}`);
      }
      await cargar();
    } catch (err) {
      setMensaje(err instanceof Error ? err.message : "Error al guardar la programacion");
    }
  };

  const calcularAhora = async () => {
    setCalculando(true);
    setMensaje(null);
    try {
      const res = await api<ResultadoRecalculo>("/indicadores/recalculo", { method: "POST" });
      setResultado(res);
      setMensaje(`Calculo manual finalizado: ${res.calculados} indicadores recalculados`);
      await cargar();
    } catch (err) {
      setMensaje(err instanceof Error ? err.message : "Error al ejecutar el calculo");
    } finally {
      setCalculando(false);
    }
  };

  if (!cargado) return null;

  if (!puede("config")) {
    return (
      <div className="min-h-screen">
        <Sidebar />
        <div className="ml-64 p-6">
          <Card className="text-center py-10 text-muted-foreground">
            Tu rol no tiene acceso a la programacion del calculo (RF-04).
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Sidebar />
      <div className="ml-64 p-6 space-y-4">
        <h1 className="text-xl font-bold">Calculo de indicadores</h1>
        <p className="text-sm text-muted-foreground">
          Frecuencia con la que el sistema vuelve a tomar los datos de las fuentes institucionales
          y recalcula los indicadores.
        </p>

        {mensaje && (
          <div className="bg-accent text-accent-foreground text-sm rounded-lg px-3 py-2">{mensaje}</div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Card className="lg:col-span-2">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base">Programacion actual</CardTitle>
                  <CardDescription>{estado?.frecuencia ?? "Cargando..."}</CardDescription>
                  <div className="text-xs text-muted-foreground mt-1">
                    Proxima ejecucion:{" "}
                    {estado?.proxima_ejecucion
                      ? new Date(estado.proxima_ejecucion).toLocaleString("es-CU")
                      : "no disponible"}
                  </div>
                </div>
                <Badge variant={estado?.intervalo_horas ? "success" : "secondary"}>
                  {estado?.intervalo_horas ? `cada ${estado.intervalo_horas} h` : "diario"}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4 border-t pt-4">
              <RadioGroup value={modo} onValueChange={(v) => setModo(v as "intervalo" | "diario")} className="space-y-3">
                <div className="flex items-center gap-2 text-sm">
                  <RadioGroupItem value="intervalo" id="modo-intervalo" />
                  <Label htmlFor="modo-intervalo">Cada N horas</Label>
                  <select
                    className="h-9 rounded-md border border-input bg-card px-2 text-sm shadow-sm"
                    value={intervalo}
                    disabled={modo !== "intervalo"}
                    onChange={(e) => setIntervalo(Number(e.target.value))}
                  >
                    {INTERVALOS.map((n) => (
                      <option key={n} value={n}>
                        cada {n} h
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <RadioGroupItem value="diario" id="modo-diario" />
                  <Label htmlFor="modo-diario">Todos los dias a las</Label>
                  <Input
                    type="time"
                    className="h-9 w-32"
                    value={hora}
                    disabled={modo !== "diario"}
                    onChange={(e) => setHora(e.target.value)}
                  />
                </div>
              </RadioGroup>
              <Button onClick={() => void guardar()}>Guardar programacion</Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Ejecutar ahora</CardTitle>
              <CardDescription>
                Lanza el recalculo manual de todos los indicadores activos (datos de las fuentes
                vigentes) sin esperar la proxima ejecucion programada.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                onClick={() => void calcularAhora()}
                disabled={calculando || !puede("recalcular")}
                variant="secondary"
              >
                {calculando ? "Calculando..." : "Calcular ahora"}
              </Button>
              {resultado && (
                <div className="text-sm border-t pt-3 space-y-1">
                  <div>
                    Indicadores recalculados: <strong>{resultado.calculados}</strong>
                  </div>
                  <div>
                    Errores: <strong>{resultado.errores}</strong>
                  </div>
                  {resultado.detalles.length > 0 && (
                    <ul className="text-xs text-destructive list-disc pl-4">
                      {resultado.detalles.map((d) => (
                        <li key={d}>{d}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
