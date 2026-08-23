import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 px-6 text-center">
      <div className="space-y-3">
        <p className="font-mono text-sm uppercase tracking-[0.3em] text-primary">
          Anahita
        </p>
        <h1 className="text-4xl font-bold sm:text-5xl">
          Gerencie suas campanhas de D&D 5e
        </h1>
        <p className="mx-auto max-w-xl text-muted-foreground">
          Fichas de personagem, combate em tempo real, world-building e
          catálogo do SRD — tudo em um só lugar para DMs e jogadores.
        </p>
      </div>
      <div className="flex flex-col gap-3 sm:flex-row">
        <Link
          href="/auth/login"
          className="rounded-md bg-primary px-6 py-2.5 font-medium text-primary-foreground transition-opacity hover:opacity-90"
        >
          Entrar
        </Link>
        <Link
          href="/auth/register"
          className="rounded-md border border-border px-6 py-2.5 font-medium transition-colors hover:bg-secondary"
        >
          Criar conta
        </Link>
      </div>
    </main>
  );
}
