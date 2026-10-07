import type { Category } from "../api/client";

interface Props {
  categories: Category[];
  value: number | null;
  onChange: (id: number) => void;
  label?: string;
}

export function LabelDropdown({ categories, value, onChange, label = "Category" }: Props) {
  return (
    <label className="row">
      <span>{label}</span>
      <select value={value ?? ""} onChange={(e) => onChange(Number(e.target.value))}>
        <option value="" disabled>
          choose…
        </option>
        {categories.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name}
          </option>
        ))}
      </select>
    </label>
  );
}
