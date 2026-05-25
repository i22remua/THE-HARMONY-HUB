import 'package:flutter/material.dart';

class PresetMode {
  final String id;
  final String title;
  final String subtitle;
  final String description;
  final IconData icon;
  final String spotifyPlaylistUrl;
  final String goal;
  final String suggestedMood;
  final String suggestedOutcome;

  const PresetMode({
    required this.id,
    required this.title,
    required this.subtitle,
    required this.description,
    required this.icon,
    required this.spotifyPlaylistUrl,
    required this.goal,
    required this.suggestedMood,
    required this.suggestedOutcome,
  });
}