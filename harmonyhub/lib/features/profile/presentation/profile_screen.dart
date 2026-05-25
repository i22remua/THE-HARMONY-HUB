import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:harmonyhub/core/navigation/harmony_route.dart';
import 'package:harmonyhub/core/widgets/editorial_surfaces.dart';
import 'package:harmonyhub/core/widgets/home_shortcut_button.dart';
import 'package:harmonyhub/core/widgets/staggered_reveal.dart';
import 'package:harmonyhub/features/profile/presentation/profile_detail_screen.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  Widget _menuTile({
    required BuildContext context,
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
  }) {
    return EditorialPanel(
      radius: 26,
      padding: EdgeInsets.zero,
      accentColor: const Color(0xFF1E4B43),
      child: InkWell(
        borderRadius: BorderRadius.circular(26),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: const Color(0xFFE4EFE8),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Icon(icon, color: const Color(0xFF204F46)),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        fontSize: 17,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      subtitle,
                      style: const TextStyle(
                        color: Color(0xFF5E645F),
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              const Icon(Icons.chevron_right_rounded),
            ],
          ),
        ),
      ),
    );
  }

  Widget _guideStep({
    required IconData icon,
    required String title,
    required String text,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFFFFCF8),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: const Color(0xFFE7DBCD)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: const Color(0xFFE4EFE8),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Icon(icon, color: const Color(0xFF204F46)),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontWeight: FontWeight.w700,
                    fontSize: 16,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  text,
                  style: const TextStyle(
                    color: Color(0xFF5E645F),
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _faqItem({
    required String question,
    required String answer,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: const Color(0xFFFFFCF8),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: const Color(0xFFE7DBCD)),
      ),
      child: Theme(
        data: ThemeData(dividerColor: Colors.transparent),
        child: ExpansionTile(
          tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
          title: Text(
            question,
            style: const TextStyle(
              fontWeight: FontWeight.w700,
              color: Color(0xFF1F2421),
            ),
          ),
          children: [
            Text(
              answer,
              style: const TextStyle(
                color: Color(0xFF5E645F),
                height: 1.45,
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final user = FirebaseAuth.instance.currentUser;

    return Scaffold(
      body: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFFF8F1E8), Color(0xFFF1E7DA), Color(0xFFE7EDE7)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 18, 20, 120),
            children: [
              Row(
                children: [
                  const Expanded(
                    child: Text(
                      'Perfil',
                      style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFF1F2421),
                      ),
                    ),
                  ),
                  const HomeShortcutButton(),
                ],
              ),
              const SizedBox(height: 18),
              StaggeredReveal(
                order: 0,
                child: Container(
                padding: const EdgeInsets.fromLTRB(22, 22, 22, 24),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(30),
                  gradient: const LinearGradient(
                    colors: [
                      Color(0xFF204F46),
                      Color(0xFF35685F),
                      Color(0xFFE8D7C7),
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x22000000),
                      blurRadius: 24,
                      offset: Offset(0, 12),
                    ),
                  ],
                ),
                child: Stack(
                  children: [
                    Positioned(
                      top: -10,
                      right: -10,
                      child: Container(
                        width: 104,
                        height: 104,
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.1),
                          shape: BoxShape.circle,
                        ),
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'TU PERFIL',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 11,
                            letterSpacing: 1.5,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(height: 14),
                        Text(
                          user?.email ?? 'Cuenta activa',
                          style: Theme.of(context).textTheme.headlineSmall
                              ?.copyWith(
                                color: Colors.white,
                                fontSize: 30,
                                height: 0.98,
                              ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              ),
              const SizedBox(height: 16),
              StaggeredReveal(
                order: 1,
                child: _menuTile(
                context: context,
                icon: Icons.library_music_outlined,
                title: 'Spotify',
                subtitle:
                    'Revisar la conexión que usa la app para generar tus playlists reales.',
                onTap: () {
                  HapticFeedback.selectionClick();
                  Navigator.push(
                    context,
                    buildHarmonyRoute(
                      const ProfileDetailScreen(
                        title: 'Spotify',
                        icon: Icons.library_music_outlined,
                        eyebrow: 'CONEXION MUSICAL',
                        showSpotifyConnect: true,
                        points: [
                          'Conectar o reconectar tu cuenta cuando lo necesites.',
                          'Usar tus gustos recientes para personalizar mejor las playlists.',
                          'Abrir directamente en Spotify la sesión que acabas de generar.',
                        ],
                      ),
                    ),
                  );
                },
              ),
              ),
              const SizedBox(height: 12),
              StaggeredReveal(
                order: 2,
                child: _menuTile(
                context: context,
                icon: Icons.lock_outline_rounded,
                title: 'Privacidad',
                subtitle:
                    'Cómo se guardan tus check-ins, tu historial emocional y tus preferencias.',
                onTap: () {
                  HapticFeedback.selectionClick();
                  Navigator.push(
                    context,
                    buildHarmonyRoute(
                      const ProfileDetailScreen(
                        title: 'Privacidad',
                        icon: Icons.lock_outline_rounded,
                        eyebrow: 'CUIDADO DE TUS DATOS',
                        points: [
                          'Tus check-ins y tu historial se vinculan a tu cuenta autenticada.',
                          'La parte emocional sensible se separa del bloque público mínimo.',
                          'Solo se usan los datos necesarios para personalizar y aprender de las sesiones.',
                        ],
                      ),
                    ),
                  );
                },
              ),
              ),
              const SizedBox(height: 16),
              StaggeredReveal(
                order: 3,
                child: EditorialPanel(
                  accentColor: const Color(0xFF1E4B43),
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const EditorialSectionHeader(
                          eyebrow: 'GUIA RAPIDA',
                          title: 'Cómo sacarle partido a Harmony Hub',
                          subtitle:
                              'Una guía breve pero visible reduce fricción mejor que obligarte a descubrir el flujo por prueba y error.',
                        ),
                        const SizedBox(height: 14),
                        _guideStep(
                          icon: Icons.favorite_outline,
                          title: '1. Entra con un check-in breve y honesto',
                          text:
                              'No hace falta redactar mucho. Lo importante es marcar bien cómo vienes, qué buscas y qué resultado te gustaría notar al terminar.',
                        ),
                        const SizedBox(height: 10),
                        _guideStep(
                          icon: Icons.hearing_outlined,
                          title: '2. Decide si quieres meter el entorno',
                          text:
                              'Si el ruido o el contexto importan de verdad en ese momento, activa la escucha. Si no, puedes dejar que la sesión se apoye solo en el check-in.',
                        ),
                        const SizedBox(height: 10),
                        _guideStep(
                          icon: Icons.graphic_eq_outlined,
                          title: '3. Revisa la recomendación antes de generar',
                          text:
                              'La pantalla de recomendación resume el tono, la energía y el tipo de salida que Harmony Hub está proponiendo. Si no encaja, es mejor rehacer antes de crear playlist.',
                        ),
                        const SizedBox(height: 10),
                        _guideStep(
                          icon: Icons.queue_music_outlined,
                          title: '4. Genera la playlist y escúchala fuera',
                          text:
                              'La selección parte del catálogo curado y luego se materializa en Spotify para que puedas escucharla como una playlist real y no solo como una sugerencia abstracta.',
                        ),
                        const SizedBox(height: 10),
                        _guideStep(
                          icon: Icons.rate_review_outlined,
                          title: '5. Cierra el ciclo con feedback útil',
                          text:
                              'Marca si te ayudó, cómo te dejó y si esa sesión te representa de verdad. Ese cierre es lo que convierte uso en aprendizaje acumulado.',
                        ),
                        const SizedBox(height: 10),
                        _guideStep(
                          icon: Icons.history_outlined,
                          title: '6. Usa historial y aprendizaje para comparar',
                          text:
                              'El historial te sirve para ver qué tipo de sesiones te funcionan mejor y la pantalla de aprendizaje para entender si el sistema ya se está apoyando más en memoria o sigue siendo prudente.',
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 12),
              StaggeredReveal(
                order: 5,
                child: EditorialPanel(
                  accentColor: const Color(0xFFC8845A),
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const EditorialSectionHeader(
                          eyebrow: 'FAQ',
                          title: 'Preguntas frecuentes',
                          subtitle:
                              'La ayuda más útil suele responder dudas frecuentes, estar cerca de la acción y evitar tecnicismos innecesarios.',
                        ),
                        const SizedBox(height: 14),
                        _faqItem(
                          question: '¿Por qué tengo que conectar Spotify?',
                          answer:
                              'Porque Harmony Hub usa Spotify para crear una playlist real y reproducible a partir de la selección final del catálogo.',
                        ),
                        _faqItem(
                          question: '¿Qué pasa si no dejo feedback?',
                          answer:
                              'La sesión sirve como contexto puntual, pero el sistema aprende mucho menos sobre qué te funcionó de verdad.',
                        ),
                        _faqItem(
                          question: '¿El entorno siempre cambia la recomendación?',
                          answer:
                              'No. Solo entra como señal real cuando la lectura es suficientemente útil; si no, se mantiene como referencia prudente.',
                        ),
                        _faqItem(
                          question: '¿Cuándo merece la pena rehacer el check-in?',
                          answer:
                              'Cuando la recomendación se aleja claramente de lo que necesitas o cuando respondiste demasiado rápido y el resultado no refleja bien tu momento real.',
                        ),
                        _faqItem(
                          question: '¿Qué significa que el aprendizaje tenga más peso?',
                          answer:
                              'Que Harmony Hub ya ha acumulado suficientes sesiones con feedback como para apoyarse más en patrones que te han funcionado antes, en lugar de depender solo del contexto de hoy.',
                        ),
                        _faqItem(
                          question: '¿La app elige canciones con inteligencia artificial?',
                          answer:
                              'No exactamente. El aprendizaje automático se usa sobre todo para ajustar el tipo de sesión que más te conviene. Después, la selección musical se construye sobre un catálogo curado y se convierte en playlist real en Spotify.',
                        ),
                        _faqItem(
                          question: '¿Qué aprende realmente el modelo sobre mí?',
                          answer:
                              'Aprende patrones útiles de contexto: por ejemplo, qué tipo de sesión suele ayudarte más cuando estás cansado, estresado o triste, qué intensidad encaja contigo y cuánto puede apoyarse en lo ya aprendido.',
                        ),
                        _faqItem(
                          question: '¿Por qué a veces el sistema es prudente con el aprendizaje?',
                          answer:
                              'Porque no todos los estados emocionales tienen la misma cantidad de evidencia. Si un mood todavía no está maduro, la app evita sobreactuar con recuerdos poco sólidos.',
                        ),
                        _faqItem(
                          question: '¿Por qué a veces parece que aprende mucho y otras menos?',
                          answer:
                              'Porque Harmony Hub no aplica el aprendizaje igual en todos los estados emocionales. Si en un mood ya tiene suficientes sesiones útiles, lo usa con más confianza. Si todavía hay poca evidencia, se vuelve más prudente.',
                        ),
                        _faqItem(
                          question: '¿Qué hace que el modelo aprenda mejor?',
                          answer:
                              'Lo que más ayuda es repetir sesiones parecidas y cerrar el ciclo con feedback claro. Cuanto más consistente sea esa señal, más fácil es que el sistema detecte patrones útiles y los aproveche después.',
                        ),
                        _faqItem(
                          question: '¿Puede equivocarse el aprendizaje?',
                          answer:
                              'Sí. Por eso la app no se apoya ciegamente en lo aprendido. Si el contexto actual cambia mucho o la evidencia todavía es débil, combina memoria, reglas y señales del momento para no quedarse encerrada en un patrón incorrecto.',
                        ),
                        _faqItem(
                          question: '¿Qué significa que un mood todavía no esté maduro?',
                          answer:
                              'Significa que Harmony Hub aún no ha visto suficientes sesiones útiles de ese mismo estado emocional como para confiar plenamente en lo aprendido. En ese caso, la app sigue personalizando, pero con menos peso de memoria.',
                        ),
                        _faqItem(
                          question: '¿El modelo reemplaza lo que yo digo en el check-in?',
                          answer:
                              'No. El check-in sigue siendo la señal principal de cada sesión. El aprendizaje entra para matizar o reforzar esa lectura, no para ignorar lo que has contado hoy.',
                        ),
                        _faqItem(
                          question: '¿Por qué el sistema a veces usa más memoria y otras más contexto?',
                          answer:
                              'Porque intenta equilibrar ambas cosas. Si el momento actual está muy claro o el aprendizaje todavía no es sólido, pesa más el contexto. Si ya existe evidencia suficiente y el patrón se repite, sube el peso de la memoria.',
                        ),
                        _faqItem(
                          question: '¿Qué hago si falla la generación de playlist?',
                          answer:
                              'Lo más frecuente es un problema temporal con Spotify, como rate limit o materialización de canciones. Normalmente basta con esperar un poco y volver a intentarlo.',
                        ),
                        _faqItem(
                          question: '¿Se guarda todo lo que escribo?',
                          answer:
                              'Harmony Hub guarda solo la información necesaria para reconstruir tu sesión y aprender de ella, separando la parte sensible del bloque público mínimo cuando corresponde.',
                        ),
                        _faqItem(
                          question: '¿Qué diferencia hay entre presets y check-in libre?',
                          answer:
                              'Los presets sirven como atajos para momentos típicos. El check-in libre, en cambio, ajusta mejor la sesión al estado concreto en el que estás hoy.',
                        ),
                        _faqItem(
                          question: '¿Cuándo mirar historial y cuándo mirar aprendizaje?',
                          answer:
                              'Historial te ayuda a revisar qué pasó en cada sesión. Aprendizaje te ayuda a entender si el sistema ya está usando memoria acumulada y con qué intensidad.',
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
