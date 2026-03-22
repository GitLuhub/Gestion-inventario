import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Gestión de Inventario',
  description: 'Sistema de gestión de inventario avanzado con Odoo',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  )
}
