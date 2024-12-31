// pages/index.jsx

import React, { useState, useEffect } from "react";
import Head from "next/head";
import { motion } from "framer-motion";
import { FaArrowLeft, FaArrowRight } from "react-icons/fa";
import { getPlatformLogo } from "../utils/imageUtils";

const HomePage = () => {
  const [games, setGames] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loadingData, setLoadingData] = useState(true);
  const [loadingImages, setLoadingImages] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedPlatform, setSelectedPlatform] = useState("all");
  const [isDarkMode, setIsDarkMode] = useState(true);

  // Sayfalama
  const gamesPerPage = 20;

  // Görsellerin preload durumu
  const [imagesLoaded, setImagesLoaded] = useState(0);
  const [imagesTotal, setImagesTotal] = useState(0);

  // Orijinal görsel isimlerini sakladığımız dictionary
  // Key: görsel isminin küçük harfle yazılmış versiyonu
  // Value: görselin orijinal adı (büyük/küçük harfli olabilir)
  const [imageDict, setImageDict] = useState({});

  // Oyunları API'den çekmek için fonksiyon
  const fetchGames = async () => {
    setLoadingData(true);
    setError(null);
    try {
      const res = await fetch("/api/games"); // API route'unuzu güncelleyin
      if (!res.ok) throw new Error("Failed to fetch games");
      const data = await res.json();

      // Metascore’a göre yüksekten düşüğe sıralama
      const sortedData = data.sort((a, b) => b["Metascore"] - a["Metascore"]);

      setGames(sortedData);
      setLoadingData(false);
    } catch (err) {
      setError("Oyunlar yüklenemedi");
      console.error(err);
      setLoadingData(false);
    }
  };

  // Görselleri API'den çekmek ve sözlük oluşturmak
  const fetchImages = async () => {
    try {
      const res = await fetch("/api/images"); // Oluşturduğunuz API route
      if (!res.ok) throw new Error("Failed to fetch images");
      const data = await res.json();

      setImagesTotal(data.images.length);

      // 1) Dictionary oluşturuyoruz
      //    "halo.jpg" -> "Halo.JPG"
      //    "elden ring.jpg" -> "Elden Ring.JPG"
      const tempDict = {};
      data.images.forEach((originalName) => {
        const lowerKey = originalName.toLowerCase(); 
        tempDict[lowerKey] = originalName; // Key=küçük harfli, Value=orijinal ad
      });
      setImageDict(tempDict);

      // 2) Preload işlemi
      data.images.forEach((originalName) => {
        const img = new Image();
        img.src = `/gorseller/${originalName}`;
        img.onload = () => {
          setImagesLoaded((prev) => prev + 1);
        };
        img.onerror = () => {
          console.error(`Görsel yüklenemedi: /gorseller/${originalName}`);
          setImagesLoaded((prev) => prev + 1);
        };
      });
    } catch (err) {
      console.error(err);
      setError("Görseller yüklenemedi");
      setLoadingImages(false);
    }
  };

  // Oyunları ve görselleri yüklemek için useEffect
  useEffect(() => {
    fetchGames();
    fetchImages();
  }, []);

  // Görsellerin yüklenme durumunu kontrol etmek için useEffect
  useEffect(() => {
    if (imagesLoaded === imagesTotal && imagesTotal > 0) {
      setLoadingImages(false);
    }
  }, [imagesLoaded, imagesTotal]);

  // Tema değiştirme fonksiyonu
  const toggleTheme = () => setIsDarkMode((prev) => !prev);

  // Yüklenme yüzdesi
  const loadingPercentage =
    imagesTotal > 0 ? Math.round((imagesLoaded / imagesTotal) * 100) : 0;

  // Oyun ismini temizleme fonksiyonu
  const sanitizeGameName = (gameName) => {
    let sanitized = gameName.replace(/[\®\™]/g, "");
    const suffixesToRemove = [
      "Digital Deluxe Edition Upgrade",
      "Game of the Year Edition",
      "GOTY Edition",
      "Deluxe Edition",
      "Ultimate Edition",
      "Expansion Pack",
      "Bundle",
      "Special Edition",
      "Remastered",
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
    sanitized = sanitized.replace(/[:]/g, "");
    sanitized = sanitized.replace(/\s+/g, " ").trim();
    return sanitized;
  };

  // 1) Platform filtreleme
  const platformFilteredGames =
    selectedPlatform === "all"
      ? games
      : games.filter((game) =>
          (selectedPlatform === "steam" && game["Steam Price"]) ||
          (selectedPlatform === "epic" && game["Epic Price"])
        );

  // 2) Arama filtresi
  const searchFilteredGames = searchQuery
    ? platformFilteredGames.filter((game) =>
        game["Game Name"].toLowerCase().includes(searchQuery.toLowerCase())
      )
    : platformFilteredGames;

  // 3) Görseli olmayan oyunları ayıklama
  const finalGames = searchFilteredGames.filter((game) => {
    const sanitizedName = sanitizeGameName(game["Game Name"]);
    // .jpg ekleyip küçük harfe çeviriyoruz
    const lowerImgKey = `${sanitizedName}.jpg`.toLowerCase();
    // Dictionary'de varsa (yani orijinal dosya adını bulduysak) bu oyun kalsın
    return Boolean(imageDict[lowerImgKey]);
  });

  // 4) ID atama
  const finalGamesWithId = finalGames.map((game, index) => ({
    ...game,
    id: index + 1,
  }));

  // 5) Sayfalama
  const totalPages = Math.ceil(finalGamesWithId.length / gamesPerPage);
  const startIndex = (currentPage - 1) * gamesPerPage;
  const endIndex = startIndex + gamesPerPage;
  const paginatedGames = finalGamesWithId.slice(startIndex, endIndex);

  return (
    <>
      <Head>
        <title>My Game Store</title>
        <meta
          name="description"
          content="Oyun fiyatlarını karşılaştırın ve en uygun fiyatları bulun."
        />
        <link rel="icon" href="/gorseller/mygamestorelogo.png" />
      </Head>

      <div
        className={`min-h-screen ${
          isDarkMode ? "bg-gray-900 text-white" : "bg-gray-100 text-black"
        } bg-cover bg-center bg-no-repeat`}
        style={{
          backgroundImage: isDarkMode
            ? "url('/gorseller/sitewallpaper.jpg')"
            : "none",
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      >
        {loadingData || loadingImages ? (
          <div className="flex justify-center items-center min-h-screen">
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 border-4 border-indigo-500 border-dashed rounded-full animate-spin"></div>
              <p className="mt-4 text-xl text-indigo-500">
                Oyunlar yükleniyor...
              </p>
              <p className="mt-2 text-lg text-indigo-500">
                Yükleme Yüzdesi: {loadingPercentage}%
              </p>
            </div>
          </div>
        ) : (
          <>
            {/* Üst Kısım */}
            <div className="py-6">
              <div className="container mx-auto flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <img
                    src="/gorseller/mygamestorelogo.png"
                    alt="My Game Store Logo"
                    className="w-16 h-16 rounded-full"
                  />
                  <div>
                    <h1 className="text-4xl font-extrabold text-indigo-400">
                      My Game Store
                    </h1>
                    <p className="text-md text-gray-300">
                      En iyi oyun fiyatlarını karşılaştırın ve en uygun
                      fırsatları yakalayın.
                    </p>
                  </div>
                </div>
                <button
                  onClick={toggleTheme}
                  className="px-4 py-2 rounded-lg bg-indigo-500 text-white hover:bg-indigo-600 transition-all"
                >
                  {isDarkMode ? "Açık Tema" : "Koyu Tema"}
                </button>
              </div>
            </div>

            {/* Arama ve Filtreler */}
            <div className="container mx-auto p-6">
              <div className="flex justify-between items-center mb-6">
                <motion.div
                  className="relative w-1/2"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 1, duration: 0.5 }}
                >
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Oyunu Ara..."
                    className={`w-full px-4 py-3 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                      isDarkMode
                        ? "bg-gray-800 text-white"
                        : "bg-gray-200 text-black"
                    } placeholder-gray-400`}
                  />
                </motion.div>

                <div className="flex space-x-4">
                  <button
                    onClick={() => setSelectedPlatform("all")}
                    className={`px-4 py-2 rounded-lg ${
                      selectedPlatform === "all"
                        ? "bg-indigo-500 text-white"
                        : "bg-gray-300 text-black"
                    } hover:bg-indigo-600 transition-all`}
                  >
                    Tüm Platformlar
                  </button>
                  <button
                    onClick={() => setSelectedPlatform("steam")}
                    className={`px-4 py-2 rounded-lg ${
                      selectedPlatform === "steam"
                        ? "bg-indigo-500 text-white"
                        : "bg-gray-300 text-black"
                    } hover:bg-indigo-600 transition-all`}
                  >
                    Steam
                  </button>
                  <button
                    onClick={() => setSelectedPlatform("epic")}
                    className={`px-4 py-2 rounded-lg ${
                      selectedPlatform === "epic"
                        ? "bg-indigo-500 text-white"
                        : "bg-gray-300 text-black"
                    } hover:bg-indigo-600 transition-all`}
                  >
                    Epic Games
                  </button>
                </div>
              </div>

              {/* Hata Mesajı */}
              {error ? (
                <motion.p
                  className="text-center text-red-500 text-lg"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 1.5, duration: 0.5 }}
                >
                  {error}
                </motion.p>
              ) : (
                // Tablo
                <motion.div
                  className={`overflow-x-auto ${
                    isDarkMode ? "bg-gray-800" : "bg-gray-200"
                  } shadow-lg rounded-lg`}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 2, duration: 1 }}
                >
                  <table
                    className={`min-w-full rounded-lg overflow-hidden ${
                      isDarkMode ? "bg-gray-800" : "bg-gray-200"
                    }`}
                  >
                    <thead>
                      <tr
                        className={`${
                          isDarkMode
                            ? "bg-gray-700 text-gray-200"
                            : "bg-gray-300 text-black"
                        } text-lg font-bold uppercase tracking-wide`}
                      >
                        <th className="py-3 px-6 text-left">ID</th>
                        <th className="py-3 px-6 text-left">Oyun Adı</th>
                        <th className="py-3 px-6 text-left">Fiyatlar</th>
                        <th className="py-3 px-6 text-left">Metascore</th>
                      </tr>
                    </thead>
                    <tbody>
                      {paginatedGames.map((game) => {
                        // Artık ID'ler kesintisiz
                        // Tabloda, "game.id" = "index + 1" ile atadığımız değer
                        const sanitizedName = sanitizeGameName(game["Game Name"]);
                        const lowerImgKey = `${sanitizedName}.jpg`.toLowerCase();
                        const originalImageName = imageDict[lowerImgKey]; 
                        // Bu noktada originalImageName kesinlikle var
                        // çünkü filter'da olmayanları zaten eledik.

                        return (
                          <motion.tr
                            key={game.id}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ duration: 0.3 }}
                            whileHover={{ scaleY: 1.05 }}
                            className={`${
                              isDarkMode
                                ? "hover:bg-gray-700"
                                : "hover:bg-gray-400"
                            } text-lg font-semibold transition-transform duration-300`}
                          >
                            <td className="py-4 px-6">{game.id}</td>
                            <td className="py-4 px-6 flex items-center space-x-4">
                              <img
                                src={`/gorseller/${originalImageName}`}
                                alt={game["Game Name"]}
                                className="w-16 h-16 object-cover rounded-lg"
                              />
                              <span className="text-xl font-bold">
                                {game["Game Name"]}
                              </span>
                            </td>
                            <td className="py-4 px-6">
                              {game["Steam Price"] && game["Steam URL"] && (
                                <a
                                  href={game["Steam URL"]}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex items-center space-x-2 hover:scale-110 hover:shadow-md transition-transform duration-300"
                                >
                                  <img
                                    src={getPlatformLogo("steam")}
                                    alt="Steam Logo"
                                    className="w-6 h-6"
                                  />
                                  <span>{game["Steam Price"]}</span>
                                </a>
                              )}
                              {game["Epic Price"] && game["Epic URL"] && (
                                <a
                                  href={game["Epic URL"]}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex items-center space-x-2 mt-2 hover:scale-110 hover:shadow-md transition-transform duration-300"
                                >
                                  <img
                                    src={getPlatformLogo("epic")}
                                    alt="Epic Logo"
                                    className="w-6 h-6"
                                  />
                                  <span>{game["Epic Price"]}</span>
                                </a>
                              )}
                            </td>
                            <td className="py-4 px-6">
                              <div className="w-16 h-16 bg-green-600 rounded-lg flex items-center justify-center text-white text-lg font-bold">
                                {game["Metascore"]}
                              </div>
                            </td>
                          </motion.tr>
                        );
                      })}
                    </tbody>
                  </table>
                </motion.div>
              )}

              {/* Sayfa Değiştirme Kontrolleri */}
              <div className="flex justify-between items-center mt-8">
                <button
                  onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
                  disabled={currentPage === 1}
                  className="px-4 py-2 bg-indigo-500 text-white rounded-full hover:bg-indigo-600 disabled:opacity-50 flex items-center"
                >
                  <FaArrowLeft />
                </button>

                <select
                  value={currentPage}
                  onChange={(e) => setCurrentPage(Number(e.target.value))}
                  className={`px-4 py-2 ${
                    isDarkMode ? "bg-gray-700" : "bg-gray-300"
                  } text-white border border-gray-700 rounded`}
                >
                  {Array.from({ length: totalPages }, (_, index) => (
                    <option key={index + 1} value={index + 1}>
                      Sayfa {index + 1}
                    </option>
                  ))}
                </select>

                <button
                  onClick={() =>
                    setCurrentPage((prev) => Math.min(prev + 1, totalPages))
                  }
                  disabled={currentPage === totalPages}
                  className="px-4 py-2 bg-indigo-500 text-white rounded-full hover:bg-indigo-600 disabled:opacity-50 flex items-center"
                >
                  <FaArrowRight />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );
};

export default HomePage;
