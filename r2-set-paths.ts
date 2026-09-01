
// Auto-generated R2 filename mapping
// Generated: 2026-07-17T17:45:31.343Z
// Total sets: 16

export const r2SetPaths: Record<string, string> = {
  "151": "Pokemon%20TCG/Pokemon%20TCG/151",
  "ancient-origins": "Pokemon%20TCG/Pokemon%20TCG/ancient-origins",
  "aquapolis": "Pokemon%20TCG/Pokemon%20TCG/aquapolis",
  "arceus": "Pokemon%20TCG/Pokemon%20TCG/arceus",
  "astral-radiance": "Pokemon%20TCG/Pokemon%20TCG/astral-radiance",
  "base-set": "Pokemon%20TCG/Pokemon%20TCG/base-set",
  "base-set-2": "Pokemon%20TCG/Pokemon%20TCG/base-set-2",
  "battle-styles": "Pokemon%20TCG/Pokemon%20TCG/battle-styles",
  "best-of-game": "Pokemon%20TCG/Pokemon%20TCG/best-of-game",
  "black-bolt": "Pokemon%20TCG/Pokemon%20TCG/black-bolt",
  "black-white-energy-2011-unnumbered": "Pokemon%20TCG/Pokemon%20TCG/black-white-energy-2011-unnumbered",
  "black-white-promos": "Pokemon%20TCG/Pokemon%20TCG/black-white-promos",
  "black-white-trainer-kit-excadrill": "Pokemon%20TCG/Pokemon%20TCG/black-white-trainer-kit-excadrill",
  "ascended-heroes": "ascended-heroes",
  "chaos-rising": "chaos-rising",
  "perfect-order": "perfect-order",
};

// Function to build full R2 URL for a card
export function buildR2CardUrl(cardId: string): string | null {
  // Extract set code from card ID (e.g., "me2-5-001" → "me2-5")
  const parts = cardId.split('-');
  if (parts.length < 2) return null;

  // Reconstruct set code (handles both "xy7-001" and "me2-5-001")
  let setCode = parts.slice(0, -1).join('-');

  // Map to set folder name (you'll need to build this mapping)
  const setPath = r2SetPaths[setCode];
  if (!setPath) return null;

  // Construct filename
  const filename = `${cardId.replace(/-(d{3})$/, '_en_$1_std')}.jpg`;

  return `https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev/${setPath}/${filename}`;
}
