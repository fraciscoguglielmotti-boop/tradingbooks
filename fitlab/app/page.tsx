import { Dumbbell, Footprints, HeartPulse } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-8 px-5 pb-12 pt-10">
      <header className="flex flex-col gap-1">
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
          v0 · Fase 0
        </p>
        <h1 className="font-display text-6xl uppercase leading-none tracking-tight">
          FitLab
        </h1>
        <p className="text-sm text-muted-foreground">
          Scaffold listo. Auth, rutinas y nutrición vienen en próximas fases.
        </p>
      </header>

      <section className="grid grid-cols-3 gap-3">
        <PaletteSwatch
          icon={<Dumbbell className="size-5" />}
          label="Fuerza"
          className="bg-strength text-strength-foreground"
        />
        <PaletteSwatch
          icon={<Footprints className="size-5" />}
          label="Running"
          className="bg-running text-running-foreground"
        />
        <PaletteSwatch
          icon={<HeartPulse className="size-5" />}
          label="Recovery"
          className="bg-recovery text-recovery-foreground"
        />
      </section>

      <Card>
        <CardContent className="flex items-baseline justify-between gap-4">
          <div>
            <p className="font-mono text-xs uppercase tracking-widest text-muted-foreground">
              Press banca
            </p>
            <p className="font-display text-3xl">Próximo set</p>
          </div>
          <p className="font-mono text-4xl tabular-nums">
            80<span className="text-base text-muted-foreground"> kg</span>
          </p>
        </CardContent>
      </Card>

      <footer className="mt-auto font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
        Tipografías: Anton · Manrope · JetBrains Mono
      </footer>
    </main>
  );
}

function PaletteSwatch({
  icon,
  label,
  className,
}: {
  icon: React.ReactNode;
  label: string;
  className: string;
}) {
  return (
    <div
      className={`flex aspect-square flex-col items-start justify-between rounded-lg p-3 ${className}`}
    >
      {icon}
      <span className="font-display text-sm uppercase leading-none">
        {label}
      </span>
    </div>
  );
}
