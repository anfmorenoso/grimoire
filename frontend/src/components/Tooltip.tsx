import { useState, useRef } from "react";
import { createPortal } from "react-dom";

interface Props {
  content: string;
  children: React.ReactNode;
}

interface Pos {
  left: number;
  top: number;
  anchor: "top" | "bottom";
}

export default function Tooltip({ content, children }: Props) {
  const [pos, setPos] = useState<Pos | null>(null);
  const triggerRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const show = () => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    const left = Math.max(8, Math.min(rect.left + rect.width / 2 - 140, window.innerWidth - 288));
    const showBelow = rect.top < 120;
    setPos(
      showBelow
        ? { left, top: rect.bottom + 8, anchor: "top" }
        : { left, top: rect.top - 8, anchor: "bottom" }
    );
  };

  const hide = () => {
    setPos(null);
    if (timerRef.current) clearTimeout(timerRef.current);
  };

  const onTouchStart = () => {
    timerRef.current = setTimeout(show, 500);
  };

  const onTouchEnd = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
  };

  return (
    <div
      ref={triggerRef}
      className="contents"
      onMouseEnter={show}
      onMouseLeave={hide}
      onTouchStart={onTouchStart}
      onTouchEnd={onTouchEnd}
      onTouchMove={onTouchEnd}
    >
      {children}
      {pos &&
        createPortal(
          <>
            <div className="fixed inset-0 z-40" onClick={hide} />
            <div
              className="fixed z-50 w-[280px] bg-surface border border-border rounded-lg p-3 text-xs text-gray-300 shadow-xl leading-relaxed pointer-events-none"
              style={
                pos.anchor === "top"
                  ? { top: pos.top, left: pos.left }
                  : { bottom: window.innerHeight - pos.top, left: pos.left }
              }
            >
              {content}
            </div>
          </>,
          document.body
        )}
    </div>
  );
}
