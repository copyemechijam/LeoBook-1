import 'package:flutter/material.dart';

class AppColors {
  // ─── Brand ───────────────────────────────────────────────
  static const Color primary = Color(0xFF4A9EF7); // Softened modern blue
  static const Color electricBlue = primary;

  // ─── Backgrounds ─────────────────────────────────────────
  static const Color backgroundLight = Color(0xFFF0F2F5);
  static const Color backgroundDark = Color(0xFF0A0E14); // Deep dark base
  static const Color surfaceDark = Color(0xFF0F1318);

  // ─── Glass Tokens ────────────────────────────────────────
  static const Color glassDark = Color(0x80FFFFFF); // white 50%
  static const Color glassLight = Color(
    0x80FFFFFF,
  ); // white 50% (Unified for a cleaner translucent look)
  static const Color glassBorderDark = Color(0x33FFFFFF); // white 20%
  static const Color glassBorderLight = Color(0x1A000000); // black 10%
  static const Color cardDark = Color(0xFF151C24); // Slightly lighter than bg

  // ─── States & Semantic ───────────────────────────────────
  static const Color liveRed = Color(0xFFFF3B30);
  static const Color successGreen = Color(0xFF34C759);
  static const Color accentBlue = Color(0xFF00D2FF);
  static const Color warning = Color(0xFFEAB308);
  static const Color success = successGreen;

  // ─── Text ────────────────────────────────────────────────
  static const Color textDark = Color(0xFF0F172A);
  static const Color textLight = Color(0xFFF1F5F9);
  static const Color textGrey = Color(0xFF64748B);

  // ─── Accents ─────────────────────────────────────────────
  static const Color aiPurple = Color(0xFF8B5CF6);
  static const Color accentYellow = Color(0xFFFFCC00);
}
