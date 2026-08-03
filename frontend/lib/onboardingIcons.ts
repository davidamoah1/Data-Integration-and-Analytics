import {
  Building2, Users, LayoutGrid, Upload, LayoutDashboard,
  CheckCircle2, BarChart3, FileText, ScanLine, CheckSquare,
  Database, FlaskConical, Newspaper, CreditCard, Globe2,
  Sparkles, type LucideIcon,
} from 'lucide-react';

const ICON_MAP: Record<string, LucideIcon> = {
  Building2,
  Users,
  LayoutGrid,
  Upload,
  LayoutDashboard,
  CheckCircle2,
  BarChart3,
  FileText,
  ScanLine,
  CheckSquare,
  Database,
  FlaskConical,
  Newspaper,
  CreditCard,
  Globe2,
  Sparkles,
};

export function getOnboardingIcon(name: string): LucideIcon {
  return ICON_MAP[name] || Sparkles;
}
