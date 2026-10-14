"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/app/lib/auth-store";
import { Button } from "@/app/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Input } from "@/app/components/ui/input";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCargando(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: "Error de autenticacion" }));
        throw new Error(body.detail ?? "Error de autenticacion");
      }
      const data = await res.json();
      const me = await fetch(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${data.access_token}` },
      });
      const perfil = await me.json();
      useAuthStore.getState().setSesion(data.access_token, perfil);
      router.push(perfil.rol === "administrador" ? "/usuarios" : "/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setCargando(false);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center bg-green-50">
      <Card className="w-96">
        <CardHeader className="text-center">
          <CardTitle className="text-3xl font-bold text-cujae">CUJAE</CardTitle>
          <CardDescription>Cuadro de Mando Institucional</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-4">
            <Input
              placeholder="Usuario (LDAP o local)"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
            <Input
              type="password"
              placeholder="Contrasena"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            {error && <div className="text-sm text-destructive">{error}</div>}
            <Button type="submit" disabled={cargando} className="w-full">
              {cargando ? "Validando..." : "Iniciar sesion"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
