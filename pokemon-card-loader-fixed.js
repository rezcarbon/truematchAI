/**
 * Fixed Pokémon Card Loader
 * Ensures front-facing card images from R2 or pokemontcg.io
 *
 * Usage:
 * const loader = new PokemonCardLoader('xy7-001');
 * loader.getImageUrl().then(url => { img.src = url; });
 */

class PokemonCardLoader {
  constructor(cardId) {
    this.cardId = cardId;
    this.R2_URL = 'https://pub-406200aafa7c4a5d8ade973117a527a1.r2.dev';

    // Complete R2 file mapping (from auto-discovered-mapping.json)
    this.cardMapping = {
      'xy7-001': { path: 'Pokemon%20TCG/Pokemon%20TCG/ancient-origins', filename: 'en_US-XY7-001-oddish.jpg' },
      // ... (all 14,286 mappings here in production)
    };
  }

  /**
   * Get the correct image URL for this card
   * Priority: R2 (from mapping) → pokemontcg.io (front face)
   */
  async getImageUrl() {
    // Try R2 first if we have a mapping
    const mapping = this.cardMapping[this.cardId];
    if (mapping) {
      const r2Url = `${this.R2_URL}/${mapping.path}/${mapping.filename}`;
      if (await this.isUrlAccessible(r2Url)) {
        return r2Url;
      }
    }

    // Fallback: pokemontcg.io (FRONT FACE - no _back suffix)
    // Format: https://images.pokemontcg.io/cards/{cardId}.png
    return `https://images.pokemontcg.io/cards/${this.cardId}.png`;
  }

  /**
   * Check if URL is accessible (doesn't throw 404/403)
   */
  async isUrlAccessible(url) {
    try {
      const response = await fetch(url, { method: 'HEAD' });
      return response.ok;
    } catch {
      return false;
    }
  }

  /**
   * Simple sync version for immediate display
   * (best-guess R2, fallback to pokemontcg.io)
   */
  getImageUrlSync() {
    const mapping = this.cardMapping[this.cardId];
    if (mapping) {
      return `${this.R2_URL}/${mapping.path}/${mapping.filename}`;
    }
    //  CORRECT: Front-facing card (no _back suffix)
    return `https://images.pokemontcg.io/cards/${this.cardId}.png`;
  }
}

// Usage in React component
function CardImage({ cardId }) {
  const [imageUrl, setImageUrl] = React.useState(null);

  React.useEffect(() => {
    const loader = new PokemonCardLoader(cardId);
    const url = loader.getImageUrlSync();
    setImageUrl(url);
  }, [cardId]);

  return (
    <img
      src={imageUrl}
      alt={cardId}
      onError={(e) => {
        //  CORRECT fallback if R2 fails
        e.target.src = `https://images.pokemontcg.io/cards/${cardId}.png`;
      }}
    />
  );
}

// Usage in vanilla JS
function displayCard(containerId, cardId) {
  const loader = new PokemonCardLoader(cardId);
  const img = document.createElement('img');
  img.src = loader.getImageUrlSync();

  // Fallback to front-facing pokemontcg.io if R2 fails
  img.onerror = () => {
    img.src = `https://images.pokemontcg.io/cards/${cardId}.png`;
  };

  document.getElementById(containerId).appendChild(img);
}
