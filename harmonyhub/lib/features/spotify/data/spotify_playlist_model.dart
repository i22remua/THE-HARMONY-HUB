class SpotifyPlaylistModel {
  final String id;
  final String name;
  final String? description;
  final String? url;
  final int tracksTotal;

  SpotifyPlaylistModel({
    required this.id,
    required this.name,
    this.description,
    this.url,
    required this.tracksTotal,
  });

  factory SpotifyPlaylistModel.fromJson(Map<String, dynamic> json) {
    return SpotifyPlaylistModel(
      id: json['id'] ?? '',
      name: json['name'] ?? '',
      description: json['description'],
      url: json['url'],
      tracksTotal: json['tracks_total'] ?? 0,
    );
  }
}