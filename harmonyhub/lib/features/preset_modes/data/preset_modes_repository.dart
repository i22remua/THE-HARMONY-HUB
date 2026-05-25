import 'package:flutter/material.dart';
import 'package:harmonyhub/features/preset_modes/domain/preset_mode.dart';

class PresetModesRepository {
  const PresetModesRepository();

  List<PresetMode> getModes() {
    return const [
      PresetMode(
        id: 'pre_estudio',
        title: 'Pre-estudio',
        subtitle: 'Prepararte para entrar en foco sin saturarte.',
        description:
            'Ideal para empezar una sesión de estudio o trabajo profundo de forma progresiva.',
        icon: Icons.menu_book_outlined,
        spotifyPlaylistUrl:
            'https://open.spotify.com/playlist/0oPyDVNdgcPFAWmOYSK7O1',
        goal: 'foco',
        suggestedMood: 'neutral',
        suggestedOutcome: 'mas_centrado',
      ),
      PresetMode(
        id: 'post_reunion',
        title: 'Post-reunión',
        subtitle: 'Bajar carga mental y recuperar claridad.',
        description:
            'Pensado para después de reuniones, clases o conversaciones intensas.',
        icon: Icons.groups_outlined,
        spotifyPlaylistUrl:
            'https://open.spotify.com/playlist/3jy1NWl0ZEFrw4ujK1tzp4',
        goal: 'relajacion',
        suggestedMood: 'estresado',
        suggestedOutcome: 'mas_ligero',
      ),
      PresetMode(
        id: 'activacion_suave',
        title: 'Activación suave',
        subtitle: 'Subir energía sin sobreestimulación.',
        description:
            'Útil cuando estás cansado o plano y quieres ganar impulso poco a poco.',
        icon: Icons.bolt_outlined,
        spotifyPlaylistUrl:
            'https://open.spotify.com/playlist/37i9dQZF1DX0vHZ8elq0UK',
        goal: 'energia',
        suggestedMood: 'cansado',
        suggestedOutcome: 'mas_despierto',
      ),
      PresetMode(
        id: 'recuperar_foco',
        title: 'Recuperar foco',
        subtitle: 'Volver a centrarte tras distracciones o fatiga mental.',
        description:
            'Modo útil cuando te cuesta retomar el hilo y necesitas reconducir la atención.',
        icon: Icons.center_focus_strong_outlined,
        spotifyPlaylistUrl:
            'https://open.spotify.com/playlist/364kNIbt5C9kiIk7v39jBh',
        goal: 'foco',
        suggestedMood: 'neutral',
        suggestedOutcome: 'mas_centrado',
      ),
      PresetMode(
        id: 'descarga_estres',
        title: 'Descarga tras estrés',
        subtitle: 'Reducir tensión y salir del estado de saturación.',
        description:
            'Pensado para momentos de sobrecarga, agobio o acumulación de tensión.',
        icon: Icons.spa_outlined,
        spotifyPlaylistUrl:
            'https://open.spotify.com/playlist/37i9dQZF1DWXe9gFZP0gtP',
        goal: 'relajacion',
        suggestedMood: 'estresado',
        suggestedOutcome: 'mas_calmado',
      ),
      PresetMode(
        id: 'descompresion_nocturna',
        title: 'Descompresión nocturna',
        subtitle: 'Cerrar el día y bajar revoluciones.',
        description:
            'Para facilitar la transición de actividad a descanso al final del día.',
        icon: Icons.nightlight_round,
        spotifyPlaylistUrl:
            'https://open.spotify.com/playlist/148XAoKGBGzJL7mrxgPTJ6',
        goal: 'relajacion',
        suggestedMood: 'cansado',
        suggestedOutcome: 'mas_calmado',
      ),
      PresetMode(
        id: 'cambio_de_chip',
        title: 'Cambio de chip',
        subtitle: 'Salir del modo trabajo y volver a tu ritmo.',
        description:
            'Pensado para ese tramo entre terminar una jornada exigente y recuperar presencia al volver a casa o cambiar de contexto.',
        icon: Icons.sync_alt_rounded,
        spotifyPlaylistUrl:
            'https://open.spotify.com/playlist/148XAoKGBGzJL7mrxgPTJ6',
        goal: 'relajacion',
        suggestedMood: 'estresado',
        suggestedOutcome: 'mas_ligero',
      ),
    ];
  }
}
