const ACTIVE_PREFIX = "arbitrator-active:";

export function activeStorageKey(userId: string): string {
  return `${ACTIVE_PREFIX}${userId}`;
}

export function readActiveId(userId: string): string | null {
  try {
    return localStorage.getItem(activeStorageKey(userId));
  } catch {
    return null;
  }
}

export function writeActiveId(userId: string, id: string | null): void {
  try {
    const key = activeStorageKey(userId);
    if (id) localStorage.setItem(key, id);
    else localStorage.removeItem(key);
  } catch {
    /* private mode */
  }
}
