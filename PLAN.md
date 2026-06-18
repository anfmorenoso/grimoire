# Plan — feature/tag-tooltips

**Goal:** On desktop, hovering a tag pill shows its full description. On mobile, a long-press (500ms) triggers the same description in a modal/popover.

---

## Context

`TagGroup.tsx` already sets `title={e.description}` on each button, which works as a native browser tooltip on desktop but does nothing on mobile. The description text lives in `vocabulary.py` and is already served via `GET /wiki` — no backend changes needed.

---

## Implementation

### 1. Build a `Tooltip.tsx` component

`frontend/src/components/Tooltip.tsx`

- Wraps any child with a relative container
- On desktop: show on `mouseenter`, hide on `mouseleave`
- On mobile: show on `touchstart` after 500ms hold (`setTimeout`), hide on `touchend` / `touchmove`
- Renders a dark popover card above (or below if near top of screen) the element
- Dismiss on tap outside

```tsx
// rough interface
interface TooltipProps {
  content: string;
  children: React.ReactNode;
}
```

### 2. Wrap each tag button in `TagGroup.tsx`

Replace the plain `<button>` with `<Tooltip content={e.description}><button ...></button></Tooltip>`.

Remove the existing `title={e.description}` prop (native tooltip conflicts on desktop).

### 3. Positioning logic

- Use `getBoundingClientRect()` on the trigger to position the popover
- Max width: `280px`, clamp to viewport edges
- Z-index above the form (`z-50`)

### 4. Style

Matches existing dark theme:
```
bg-surface border border-border rounded-lg p-3 text-xs text-gray-300 shadow-lg
```

---

## Files to touch

| File | Change |
|------|--------|
| `frontend/src/components/Tooltip.tsx` | Create — hover + long-press logic |
| `frontend/src/components/TagGroup.tsx` | Wrap buttons with `<Tooltip>`, remove `title` prop |

---

## Testing

- Desktop: hover each tag → description popover appears, disappears on mouse leave
- Mobile (or DevTools touch sim): hold tag → popover appears, release → stays, tap elsewhere → dismisses
- Near top of screen: popover opens downward instead of upward
- AI-suggested tags (with "IA" badge) also show description
