type Props = {
  value: string
  onChange: (value: string) => void
}

export function DateTimePicker({ value, onChange }: Props) {
  const setNow = () => {
    const now = new Date()
    const local = new Date(now.getTime() - now.getTimezoneOffset() * 60_000).toISOString().slice(0, 16)
    onChange(local)
  }

  return (
    <div className="flex flex-col gap-1.5 text-sm">
      <span className="font-medium text-slate-700">Travel time</span>
      <div className="grid grid-cols-[minmax(0,1fr)_auto] gap-2">
        <input
          type="datetime-local"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="min-h-11 min-w-0 rounded-md border border-slate-300 bg-white px-3 text-slate-950 outline-none transition focus:border-emerald-700 focus:ring-2 focus:ring-emerald-100"
        />
        <button
          type="button"
          onClick={setNow}
          className="min-h-11 rounded-md border border-emerald-200 bg-emerald-50 px-3 text-sm font-semibold text-emerald-800 transition hover:bg-emerald-100"
        >
          Now
        </button>
      </div>
    </div>
  )
}
