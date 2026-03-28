export default function Home() {
  return (
    <main className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center space-y-3">
        <div className="flex flex-col items-center leading-none">
          <span className="text-base font-black tracking-tight text-foreground">
            PULSE
          </span>
          <span className="text-[10px] font-light tracking-wide text-muted-foreground">
            live sentiment
          </span>
        </div>
        <p className="text-[10px] tracking-widest text-muted-foreground uppercase">
          Scaffolding complete — dataset generation in progress
        </p>
      </div>
    </main>
  )
}
