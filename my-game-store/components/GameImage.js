// components/GameImage.js

import React from 'react';

const GameImage = ({ gameName, alt, className }) => {
  // Oyun ismini temizleyerek görsel yolunu oluştur
  const sanitizeGameName = (gameName) => {
    let sanitized = gameName.replace(/[\®\™]/g, '');
    const suffixesToRemove = [
      "Digital Deluxe Edition Upgrade",
      "Game of the Year Edition",
      "GOTY Edition",
      "Deluxe Edition",
      "Ultimate Edition",
      "Expansion Pack",
      "Bundle",
      "Special Edition",
      "Anniversary Edition",
      "Collector's Edition",
      "Upgrade",
      // "Edition", // 'Edition' ifadesini kaldırmamak için yorum satırı
    ];
    const lowerCaseName = sanitized.toLowerCase();
    for (const suffix of suffixesToRemove) {
      const suffixLower = suffix.toLowerCase();
      const suffixIndex = lowerCaseName.indexOf(suffixLower);
      if (suffixIndex !== -1) {
        sanitized = sanitized.substring(0, suffixIndex).trim();
        break;
      }
    }
    sanitized = sanitized.replace(/[:]/g, '');
    sanitized = sanitized.replace(/\s+/g, ' ').trim();
    return sanitized;
  };

  const sanitizedName = sanitizeGameName(gameName);
  const imagePath = `/gorseller/${sanitizedName}.jpg`;

  return (
    <img
      src={imagePath}
      alt={alt}
      className={className}
      loading="lazy" // Performansı artırmak için lazy loading ekledik
    />
  );
};

export default GameImage;
