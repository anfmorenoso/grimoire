export interface VocabEntry {
  key: string;
  label: string;
  notion_value: string;
  description: string;
}

export interface Wiki {
  grain: VocabEntry[];
  sensations: VocabEntry[];
  masse_basse: VocabEntry[];
  role_set: VocabEntry[];
}
