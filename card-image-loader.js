/**
 * Simple Card Image Loader
 * Works with Cloudflare R2 + fallback to pokemontcg.io
 *
 * Usage:
 *   const url = getCardImageUrl('sv3-5-001');
 *   <img src={url} />
 */

// R2 Configuration
const R2_BUCKET = 'https://pokemontcg.r2.cloudflarestorage.com';
const POKEMONTCG_IO = 'https://images.pokemontcg.io/cards';

// Strategy 1: Try R2 with intelligent path guessing
function guessR2Paths(cardId) {
  // Extract set code and number
  // Examples: sv3-5-001 -> sv3-5, 001
  //           xy2-055 -> xy2, 055
  const parts = cardId.split('-');

  if (parts.length < 2) return [];

  const setCode = parts.slice(0, -1).join('-'); // Everything except last part
  const cardNumber = parts[parts.length - 1]; // Last part

  // Common path patterns we've seen
  return [
    // Pattern 1: {setCode}/{setCode}/{setCode}_en_{number}_std.jpg
    `${setCode}/${setCode}/${setCode}_en_${cardNumber}_std.jpg`,

    // Pattern 2: Pokemon TCG/Pokemon TCG/{number}/{setCode}_en_{number}_std.jpg
    `Pokemon%20TCG/Pokemon%20TCG/${cardNumber}/${setCode}_en_${cardNumber}_std.jpg`,

    // Pattern 3: Direct {setCode}_en_{number}_std.jpg
    `${setCode}_en_${cardNumber}_std.jpg`,

    // Pattern 4: With spaces (not encoded)
    `Pokemon TCG/Pokemon TCG/${cardNumber}/${setCode}_en_${cardNumber}_std.jpg`,

    // Pattern 5: Flat structure
    `${cardId}/${setCode}_en_${cardNumber}_std.jpg`,
  ];
}

// Strategy 2: Use pokemontcg.io as reliable fallback
function getFallbackUrl(cardId) {
  // pokemontcg.io uses card ID directly: sv3-5/001.png
  return `${POKEMONTCG_IO}/${cardId}.png`;
}

/**
 * Get image URL for a card
 * @param {string} cardId - Card ID (e.g., 'sv3-5-001')
 * @param {Object} options - Configuration options
 * @returns {string} Image URL (R2 or fallback)
 */
export function getCardImageUrl(cardId, options = {}) {
  const {
    preferR2 = true,
    useFallback = true,
    r2Bucket = R2_BUCKET,
  } = options;

  // Always try R2 first if preferred
  if (preferR2) {
    const possiblePaths = guessR2Paths(cardId);
    // Return first guess (in production, you'd verify these)
    if (possiblePaths.length > 0) {
      return `${r2Bucket}/${possiblePaths[0]}`;
    }
  }

  // Fallback to pokemontcg.io
  if (useFallback) {
    return getFallbackUrl(cardId);
  }

  return null;
}

/**
 * Test if URL is accessible
 * @param {string} url - URL to test
 * @returns {Promise<boolean>}
 */
export async function testUrl(url) {
  try {
    const response = await fetch(url, { method: 'HEAD', mode: 'no-cors' });
    return response.ok || response.status === 0; // 0 = no-cors response
  } catch (error) {
    return false;
  }
}

/**
 * Find working R2 URL for card (async)
 * @param {string} cardId - Card ID
 * @returns {Promise<string>} Working URL
 */
export async function findWorkingUrl(cardId) {
  const possiblePaths = guessR2Paths(cardId);

  for (const path of possiblePaths) {
    const url = `${R2_BUCKET}/${path}`;
    if (await testUrl(url)) {
      console.log(` Found working URL for ${cardId}: ${url}`);
      return url;
    }
  }

  // Fallback if no R2 URL works
  const fallbackUrl = getFallbackUrl(cardId);
  console.log(`️ Using fallback for ${cardId}: ${fallbackUrl}`);
  return fallbackUrl;
}

/**
 * Batch test multiple cards
 * @param {string[]} cardIds - Array of card IDs
 * @returns {Promise<Object>} Map of cardId -> working URL
 */
export async function findWorkingUrls(cardIds) {
  const results = {};

  for (const cardId of cardIds) {
    results[cardId] = await findWorkingUrl(cardId);
  }

  return results;
}

/**
 * Build custom R2 URL
 * Useful when you know the exact path in R2
 * @param {string} r2Path - Full path in R2 (e.g., 'pokemon-tcg/cards/sv3-5-001.jpg')
 * @returns {string} Full URL
 */
export function buildR2Url(r2Path) {
  return `${R2_BUCKET}/${r2Path}`;
}

// Export defaults
export default {
  getCardImageUrl,
  testUrl,
  findWorkingUrl,
  findWorkingUrls,
  buildR2Url,
  R2_BUCKET,
  POKEMONTCG_IO,
};
