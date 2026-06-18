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
  const isShowing = useRef(false);
  const byTouch = useRef(false);

  const show = (touch: boolean) => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    const left = Math.max(8, Math.min(rect.left + rect.width / 2 - 140, window.innerWidth - 288));
    const showBelow = rect.top < 120;
    isShowing.current = true;
    byTouch.current = touch;
    setPos(
      showBelow
        ? { left, top: rect.bottom + 8, anchor: "top" }
        : { left, top: rect.top - 8, anchor: "bottom" }
    );
  };

  const hide = () => {
    isShowing.current = false;
    setPos(null);
    if (timerRef.current) clearTimeout(timerRef.current);
  };

  const onTouchStart = () => {
    timerRef.current = setTimeout(() => show(true), 500);
  };

  const onTouchEnd = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    // If long-press triggered the tooltip, hide it when finger lifts
    if (isShowing.current) hide();
  };

  return (
    <div
      ref={triggerRef}
      onMouseEnter={() => show(false)}
      onMouseLeave={hide}
      onTouchStart={onTouchStart}
      onTouchEnd={onTouchEnd}
      onTouchMove={hide}
    >
      {children}
      {pos &&
        createPortal(
          <>
            {/* Overlay only for touch: mouse tooltips dismiss on mouseLeave, no overlay needed */}
            {byTouch.current && <div className="fixed inset-0 z-40" onClick={hide} />}
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
