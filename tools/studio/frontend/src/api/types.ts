export type StepKey = 'A' | 'V' | 'K' | 'P' | 'G' | 'D';
export type StepState = 'ok' | 'open' | 'stale' | 'na' | 'warn';

export interface ReleaseRow {
  catalog: string;
  artist: string;
  title: string;
  release_date: string | null;
  days_until: number | null;
  upcoming: boolean;
  status: Record<StepKey, StepState>;
  next: StepKey | null;
}

export type JobStatus = 'running' | 'ok' | 'failed' | 'cancelled';

export interface Job {
  id: string;
  label: string;
  status: JobStatus;
  exit_code: number | null;
  lines: string[];
  next: number;
  progress: { done: number; total: number; pct: number } | null;
}

export interface AppState {
  releases: ReleaseRow[];
  next_catalog: string;
  cdn_configured: boolean;
  cdn_missing: string[];
  genres: string[];
  releases_dirty: boolean;
  ai_configured: boolean;
  job: { id: string; status: JobStatus } | null;
}

export interface Track {
  number: number;
  title: string;
  file: string;
  duration: string;
  mp3: string;
}

export interface LocalTrack {
  number: number;
  file: string;
  title: string;
}

export interface Platform {
  name: string;
  url: string;
}

export interface ReleaseDetail {
  summary: ReleaseRow;
  release: {
    artist?: string;
    title?: string;
    genre?: string;
    release_date?: string;
    platforms?: { bandcamp?: string };
    tracks?: Track[];
  };
  entry: { platforms?: Platform[] } | null;
  about: string;
  tracks: Track[];
  local_tracks: LocalTrack[];
  problems: { validation: string[]; push: string[] };
  warnings: string[];
  files: { audio: string[]; artwork: string[]; mp3: string[]; cover: string | null; cover_large: string | null };
}

export interface PushPreview {
  target: string;
  files: { name: string; size: number }[];
  total_bytes: number;
  problems: string[];
  warnings: string[];
}

export interface DspCandidate {
  name: string;
  url: string;
  confidence: number;
  accepted: boolean;
  reason: string;
}

export interface FileResult {
  copied: string[];
  conflicts: string[];
  skipped: string[];
  unchanged: string[];
  job_id: string | null;
}
