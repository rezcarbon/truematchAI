import React, { useState, useCallback } from 'react';
import { CardImage } from './useCardImage';
import './CardGrid.css';

interface Card {
  id: string;
  name: string;
  set?: string;
  rarity?: string;
  price?: number;
}

interface CardGridProps {
  cards: Card[];
  onCardClick?: (card: Card) => void;
  columns?: number;
  loading?: boolean;
}

export const CardGrid: React.FC<CardGridProps> = ({
  cards,
  onCardClick,
  columns = 4,
  loading = false,
}) => {
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);

  const handleCardClick = useCallback(
    (card: Card) => {
      if (onCardClick) {
        onCardClick(card);
      }
    },
    [onCardClick]
  );

  if (loading) {
    return (
      <div className="card-grid-loading">
        <div className="spinner"></div>
        <p>Loading cards...</p>
      </div>
    );
  }

  if (!cards || cards.length === 0) {
    return (
      <div className="card-grid-empty">
        <p>No cards found</p>
      </div>
    );
  }

  return (
    <div className="card-grid" style={{ '--columns': columns } as React.CSSProperties}>
      {cards.map((card) => (
        <div
          key={card.id}
          className={`card-grid-item ${hoveredCard === card.id ? 'hovered' : ''}`}
          onMouseEnter={() => setHoveredCard(card.id)}
          onMouseLeave={() => setHoveredCard(null)}
          onClick={() => handleCardClick(card)}
        >
          <div className="card-image-wrapper">
            <CardImage cardId={card.id} alt={card.name} size="medium" />
            {card.price && (
              <div className="card-price">
                ${card.price.toFixed(2)}
              </div>
            )}
          </div>
          <div className="card-info">
            <h3 className="card-name">{card.name}</h3>
            {card.set && <p className="card-set">{card.set}</p>}
            {card.rarity && <p className="card-rarity"> {card.rarity}</p>}
          </div>
        </div>
      ))}
    </div>
  );
};

export default CardGrid;
