import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "TruthGPT Cloud | Plataforma de IA y Verificación Formal Z3",
  description: "Versión Cloud y SaaS de TruthGPT con suscripciones por niveles (Lite, Pro, Ultra, Enterprise), verificación matemática formal Z3 SMT y enjambres multi-agente autónomos.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="es"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-[#080914] text-[#f3f4f6]">{children}</body>
    </html>
  );
}
