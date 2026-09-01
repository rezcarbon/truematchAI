import { useMemo } from 'react';
import { r2FilenameMap, getR2ImageUrl } from './r2FilenameMap';

const POKEMONTCG_IO_URL = 'https://images.pokemontcg.io/cards';

interface CardImageOptions {
  size?: 'thumb' | 'medium' | 'hd';
  fallbackToIO?: boolean;
}

export const useCardImage = (cardId: string, options: CardImageOptions = {}) => {
  const { size = 'medium', fallbackToIO = true } = options;

  return useMemo(() => {
    // Try R2 first (URLs already properly encoded)
    const r2Url = getR2ImageUrl(cardId);
    if (r2Url) {
      return r2Url;
    }

    // Fallback to pokemontcg.io
    if (fallbackToIO) {
      return `${POKEMONTCG_IO_URL}/${cardId}.png`;
    }

    return null;
  }, [cardId, fallbackToIO]);
};

export const CardImage = ({
  cardId,
  alt = 'Pokémon Card',
  size = 'medium',
  ...props
}: {
  cardId: string;
  alt?: string;
  size?: 'thumb' | 'medium' | 'hd';
  [key: string]: any;
}) => {
  const imageUrl = useCardImage(cardId, { size });

  if (!imageUrl) {
    return (
      <div className="card-image-placeholder">
        <span>Image not found</span>
      </div>
    );
  }

  return (
    <img
      src={imageUrl}
      alt={alt}
      className={`card-image card-image-${size}`}
      loading="lazy"
      onError={(e) => {
        // If R2 fails, try pokemontcg.io
        const target = e.target as HTMLImageElement;
        if (target.src.includes('r2.cloudflarestorage')) {
          target.src = `${POKEMONTCG_IO_URL}/${cardId}.png`;
        }
      }}
      {...props}
    />
  );
};
