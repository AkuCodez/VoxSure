import type { ReactNode } from "react";

const base = { width: 20, height: 20, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, "aria-hidden": true };
const wrap = (p: ReactNode, size?: number) => <svg {...base} {...(size ? { width: size, height: size } : {})}>{p}</svg>;

export const MicIcon = ({ size }: { size?: number }) => wrap(<><rect x="9" y="3" width="6" height="11" rx="3" fill="currentColor" stroke="none" /><path d="M5 11a7 7 0 0014 0M12 18v3" /></>, size);
export const StopIcon = ({ size }: { size?: number }) => wrap(<rect x="6" y="6" width="12" height="12" rx="2.5" fill="currentColor" stroke="none" />, size);
export const SendIcon = ({ size }: { size?: number }) => wrap(<path d="M5 12l14-7-5 14-3-6-6-1z" />, size);
export const SettingsIcon = ({ size }: { size?: number }) => wrap(<><circle cx="12" cy="12" r="3" /><path d="M19 12a7 7 0 00-.1-1.2l2-1.5-2-3.4-2.3 1a7 7 0 00-2-1.2L14.2 3h-4l-.4 2.7a7 7 0 00-2 1.2l-2.3-1-2 3.4 2 1.5A7 7 0 005 12c0 .4 0 .8.1 1.2l-2 1.5 2 3.4 2.3-1c.6.5 1.3.9 2 1.2l.4 2.7h4l.4-2.7c.7-.3 1.4-.7 2-1.2l2.3 1 2-3.4-2-1.5c.1-.4.1-.8.1-1.2z" /></>, size);
export const ResetIcon = ({ size }: { size?: number }) => wrap(<path d="M4 4v6h6M20 20v-6h-6M20 10A8 8 0 006.3 6.3L4 10m16 4l-2.3 3.7A8 8 0 014 14" />, size);
export const VolumeIcon = ({ size }: { size?: number }) => wrap(<><path d="M4 9v6h4l5 4V5L8 9H4z" /><path d="M16 9a4 4 0 010 6M18.5 6.5a8 8 0 010 11" /></>, size);
export const MuteIcon = ({ size }: { size?: number }) => wrap(<><path d="M4 9v6h4l5 4V5L8 9H4z" /><path d="M17 9l5 6M22 9l-5 6" /></>, size);
export const EditIcon = ({ size }: { size?: number }) => wrap(<path d="M4 20h4L19 9l-4-4L4 16v4zM13.5 6.5l4 4" />, size);
export const CheckIcon = ({ size }: { size?: number }) => wrap(<path d="M5 12.5l4.5 4.5L19 7.5" />, size);
export const HelpIcon = ({ size }: { size?: number }) => wrap(<><circle cx="12" cy="12" r="9" /><path d="M9.5 9.5a2.5 2.5 0 114 2c-.9.6-1.5 1-1.5 2M12 17h.01" /></>, size);
export const SlashIcon = ({ size }: { size?: number }) => wrap(<><circle cx="12" cy="12" r="9" /><path d="M5.6 5.6l12.8 12.8" /></>, size);
export const PanelIcon = ({ size }: { size?: number }) => wrap(<><rect x="3" y="4" width="18" height="16" rx="3" /><path d="M15 4v16" /></>, size);
export const SparkIcon = ({ size }: { size?: number }) => wrap(<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3zM19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8L19 16z" />, size);
