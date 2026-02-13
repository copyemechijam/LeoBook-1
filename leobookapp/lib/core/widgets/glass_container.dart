import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../constants/app_colors.dart';

/// A reusable frosted-glass container inspired by Android 16's
/// semi-transparent Material You surfaces.
///
/// Features built-in hover (scale up) and click (scale down) animations.
class GlassContainer extends StatefulWidget {
  final Widget child;
  final double borderRadius;
  final EdgeInsetsGeometry? padding;
  final EdgeInsetsGeometry? margin;
  final double blurSigma;
  final Color? color;
  final Color? borderColor;
  final double borderWidth;
  final VoidCallback? onTap;
  final bool interactive;

  const GlassContainer({
    super.key,
    required this.child,
    this.borderRadius = 20,
    this.padding,
    this.margin,
    this.blurSigma = 24,
    this.color,
    this.borderColor,
    this.borderWidth = 1.0,
    this.onTap,
    this.interactive = true,
  });

  @override
  State<GlassContainer> createState() => _GlassContainerState();
}

class _GlassContainerState extends State<GlassContainer> {
  bool _isHovered = false;
  bool _isPressed = false;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    // Calculate base colors
    Color fillColor =
        widget.color ?? (isDark ? AppColors.glassDark : AppColors.glassLight);
    Color border =
        widget.borderColor ??
        (isDark ? AppColors.glassBorderDark : AppColors.glassBorderLight);

    // Adjust for states if interactive
    double scale = 1.0;
    if (widget.interactive && widget.onTap != null) {
      if (_isPressed) {
        scale = 0.98;
        fillColor = fillColor.withValues(
          alpha: (fillColor.a * 1.2).clamp(0.0, 1.0),
        );
      } else if (_isHovered) {
        scale = 1.02;
        fillColor = fillColor.withValues(
          alpha: (fillColor.a * 1.1).clamp(0.0, 1.0),
        );
      }
    }

    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: GestureDetector(
        onTapDown: (_) => setState(() => _isPressed = true),
        onTapUp: (_) => setState(() => _isPressed = false),
        onTapCancel: () => setState(() => _isPressed = false),
        onTap: () {
          if (widget.onTap != null) {
            HapticFeedback.lightImpact();
            widget.onTap!();
          }
        },
        child: AnimatedScale(
          scale: scale,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOutCubic,
          child: Container(
            margin: widget.margin,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(widget.borderRadius),
              child: BackdropFilter(
                filter: ImageFilter.blur(
                  sigmaX: widget.blurSigma,
                  sigmaY: widget.blurSigma,
                ),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  padding: widget.padding,
                  decoration: BoxDecoration(
                    color: fillColor,
                    borderRadius: BorderRadius.circular(widget.borderRadius),
                    border: Border.all(
                      color: _isHovered
                          ? AppColors.primary.withValues(alpha: 0.3)
                          : border,
                      width: widget.borderWidth,
                    ),
                    boxShadow: _isHovered
                        ? [
                            BoxShadow(
                              color: AppColors.primary.withValues(alpha: 0.1),
                              blurRadius: 15,
                              spreadRadius: 2,
                            ),
                          ]
                        : [],
                  ),
                  child: widget.child,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
