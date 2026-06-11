interface Props {
  label: string;
  description?: string;
  selected?: boolean;
  onClick?: () => void;
  color?: string;
}

export default function TagPill({ label, description, selected, onClick }: Props) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={description}
      className={`
        px-3 py-2 rounded-lg text-sm font-medium transition-all text-left
        border leading-tight min-h-[40px]
        ${selected
          ? "bg-accent text-white border-accent"
          : "bg-card text-gray-300 border-border hover:border-accent/50"
        }
      `}
    >
      {label}
    </button>
  );
}
