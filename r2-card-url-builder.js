
// R2 Set Paths - Pattern 1: Pokemon TCG folder
const r2Pattern1Sets = {
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
};

// R2 Set Paths - Pattern 2: Root level
const r2Pattern2Sets = {
  "ascended-heroes": "ascended-heroes",
  "chaos-rising": "chaos-rising",
  "perfect-order": "perfect-order",
};

// Combined mapping
const r2SetPaths = { ...r2Pattern1Sets, ...r2Pattern2Sets };

// Build R2 URL for a card ID
function buildR2CardUrl(cardId) {
  // Parse card ID: "me2-5-001" → setCode: "me2-5", cardNum: "001"
  const parts = cardId.split('-');
  if (parts.length < 2) return null;

  const cardNum = parts[parts.length - 1];
  const setCode = parts.slice(0, -1).join('-');

  const setPath = r2SetPaths[setCode];
  if (!setPath) {
    console.warn(`Unknown set code: ${setCode}`);
    return null;
  }

  // Construct filename: "me2-5-001" → "me2-5_en_001_std.jpg"
  const filename = `${setCode}_en_${cardNum}_std.jpg`;

  return `https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev/${setPath}/${filename}`;
}
