import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CUJAE | Cuadro de Mando Institucional",
  description: "Tablero de indicadores estrategicos de la Universidad Tecnologica de La Habana",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
