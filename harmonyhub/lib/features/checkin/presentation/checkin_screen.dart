import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'package:harmonyhub/core/navigation/harmony_route.dart';
import 'package:harmonyhub/core/widgets/editorial_surfaces.dart';
import 'package:harmonyhub/core/widgets/home_shortcut_button.dart';
import 'package:harmonyhub/core/widgets/staggered_reveal.dart';
import 'package:harmonyhub/features/checkin/data/checkin_firestore_service.dart';
import 'package:harmonyhub/features/checkin/data/environment_audio_decision.dart';
import 'package:harmonyhub/features/checkin/data/checkin_service.dart';
import 'package:harmonyhub/features/checkin/data/environment_audio_profile.dart';
import 'package:harmonyhub/features/checkin/data/environment_audio_service.dart';
import 'package:harmonyhub/features/checkin/presentation/guided_checkin_flow.dart';
import 'package:harmonyhub/features/recommendation/data/recommendation_firestore_service.dart';
import 'package:harmonyhub/features/recommendation/data/recommendation_service.dart';
import 'package:harmonyhub/features/recommendation/presentation/recommendation_loading_screen.dart';
import 'package:harmonyhub/features/recommendation/presentation/recommendation_screen.dart';
import 'package:harmonyhub/features/spotify/data/spotify_session.dart';

/// Pantalla de entrada principal. Recoge el estado actual del usuario mediante
/// una conversación guiada y, opcionalmente, una medición del entorno.
class CheckinScreen extends StatefulWidget {
  const CheckinScreen({super.key});

  @override
  State<CheckinScreen> createState() => _CheckinScreenState();
}

class _CheckinScreenState extends State<CheckinScreen> {
  final RecommendationService _recommendationService = RecommendationService();
  final RecommendationFirestoreService _recommendationFirestoreService =
      RecommendationFirestoreService();
  final CheckinService _checkinService = CheckinService();
  final CheckinFirestoreService _checkinFirestoreService =
      CheckinFirestoreService();
  final EnvironmentAudioService _environmentAudioService =
      EnvironmentAudioService();

  final ScrollController _scrollController = ScrollController();

  bool _started = false;
  bool _conversationCompleted = false;
  bool _asking = false;
  bool isLoading = false;
  bool isMeasuringNoise = false;

  bool _hasPendingQuestion = false;
  String? _pendingQuestionLabel;

  int _currentStep = 0;

  String mood = 'neutral';
  String goal = 'foco';
  double stressLevel = 3;
  double energyLevel = 3;

  String vocalPreference = 'indistinto';
  String intensityPreference = 'media';
  String explorationPreference = 'equilibrado';
  String popularityPreference = 'mixta';
  double sessionDurationMin = 20;

  String desiredOutcome = 'mas_calmado';

  EnvironmentAudioProfile? _audioProfile;

  double measuredDb = 0.0;
  String noiseCategory = 'quiet';

  String environmentContext = 'Sin medir';
  double environmentVariability = 0.0;
  double environmentPeakDelta = 0.0;
  double environmentConfidence = 0.0;
  bool _environmentMeasured = false;

  String _emotionAnswer = '';
  String _goalAnswer = '';
  String _energyAnswer = '';
  String _stressAnswer = '';
  String _voiceAnswer = '';
  String _intensityAnswer = '';
  String _explorationAnswer = '';
  String _popularityAnswer = '';
  String _durationAnswer = '';
  String _desiredOutcomeAnswer = '';

  final List<_ChatMessage> _messages = [];

  bool get _useEnvironmentForPersonalization =>
      _environmentMeasured;

  String get _backendNoiseCategory =>
      _useEnvironmentForPersonalization ? noiseCategory : 'moderate';

  String get _displayNoiseCategory =>
      _useEnvironmentForPersonalization ? noiseCategory : 'omitido';

  String get _environmentUsageBadge {
    if (!_environmentMeasured) return 'No medido';
    return 'Se usa para personalizar';
  }

  String get _environmentUsageRationale {
    if (!_environmentMeasured) {
      return 'Esta vez no he medido el entorno, así que la recomendación se apoya solo en tu check-in.';
    }
    return 'La lectura del entorno se incorpora como una pista real de personalización y el backend ajusta su peso según confianza, estabilidad y densidad de muestra.';
  }

  String get _environmentSummaryText {
    if (!_environmentMeasured) return 'No medido';
    final confidenceText = (environmentConfidence * 100).round();
    final stabilityText = ((_audioProfile?.stabilityScore ?? 0) * 100).round();
    return '$environmentContext · ${measuredDb.toStringAsFixed(1)} dB · conf $confidenceText% · estabilidad $stabilityText% · $_environmentUsageBadge';
  }

  String _environmentPostMeasurementMessage(EnvironmentAudioProfile profile) {
    final confidenceText = (profile.confidence * 100).round();
    final stabilityText = (profile.stabilityScore * 100).round();
    return 'Perfecto. También tendré en cuenta tu entorno: ${profile.environmentContext.toLowerCase()} (${profile.meanDb.toStringAsFixed(1)} dB, confianza $confidenceText%, estabilidad $stabilityText%). ${_environmentInterpretation(profile.environmentContext)}';
  }

  void _clearEnvironmentMeasurement() {
    _audioProfile = null;
    measuredDb = 0.0;
    noiseCategory = 'quiet';
    environmentContext = 'Sin medir';
    environmentVariability = 0.0;
    environmentPeakDelta = 0.0;
    environmentConfidence = 0.0;
    _environmentMeasured = false;
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      await _bootConversation();
    });
  }

  Future<void> _bootConversation() async {
    // Inicia la entrevista guiada que alimenta todo el resto del flujo.
    if (_started || !mounted) return;
    _started = true;

    _addAssistantMessage(
      'Hola. Vamos a hacerlo fácil, como una conversación normal.',
    );
    _addAssistantMessage(
      'Te haré unas preguntas cortas para pillarle el punto a cómo vienes hoy y prepararte una sesión que te acompañe bien.',
    );
    _addAssistantMessage(
      'No hace falta pensarlo mucho: con lo primero que te salga, me sirve.',
    );

    await Future.delayed(const Duration(milliseconds: 350));
    await _askCurrentStep();
  }

  void _addAssistantMessage(String text) {
    setState(() {
      _messages.add(_ChatMessage(text: text, isUser: false));
    });
    _scrollToBottom();
  }

  void _addUserMessage(String text) {
    setState(() {
      _messages.add(_ChatMessage(text: text, isUser: true));
    });
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent + 140,
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOut,
      );
    });
  }

  void _setPendingQuestion(String label) {
    if (!mounted) return;
    setState(() {
      _hasPendingQuestion = true;
      _pendingQuestionLabel = label;
    });
  }

  void _clearPendingQuestion() {
    if (!mounted) return;
    setState(() {
      _hasPendingQuestion = false;
      _pendingQuestionLabel = null;
    });
  }

  String _stepQuestionLabel(int step) {
    switch (step) {
      case 0:
        return '¿Cómo vienes hoy?';
      case 1:
        return '¿Qué te pide el cuerpo ahora mismo?';
      case 2:
        return '¿Cómo vas de energía ahora mismo?';
      case 3:
        return '¿Cómo notas la cabeza hoy?';
      case 4:
        return '¿Qué tipo de música te entra mejor ahora?';
      case 5:
        return '¿Con cuánta intensidad te apetece la música?';
      case 6:
        return '¿Hoy quieres que me apoye más en lo que he aprendido de ti o que abra un poco el radar?';
      case 7:
        return '¿Te tira más algo conocido o algo menos obvio?';
      case 8:
        return '¿Cuánto rato quieres que esté contigo esta sesión?';
      case 9:
        return 'Si esta sesión te sentara bien, ¿cómo te gustaría acabar?';
      case 10:
        return '¿Quieres que tenga en cuenta también lo que tienes alrededor ahora mismo?';
      default:
        return 'Continuar conversación';
    }
  }

  bool get _canGoBackOneStep {
    if (_asking || isLoading || isMeasuringNoise) return false;
    return _conversationCompleted || _currentStep > 0;
  }

  Future<void> _goBackOneStep() async {
    if (_asking) return;
    HapticFeedback.selectionClick();

    int targetStep;

    if (_conversationCompleted) {
      targetStep = 10;
      if (!mounted) return;

      setState(() {
        _conversationCompleted = false;
        _hasPendingQuestion = false;
        _pendingQuestionLabel = null;
        _currentStep = targetStep;
      });

      _addAssistantMessage(
        'Sin problema. Vamos a revisar la última respuesta antes de generar la recomendación.',
      );
    } else {
      if (_currentStep == 0) return;
      targetStep = _currentStep - 1;

      if (!mounted) return;

      setState(() {
        _hasPendingQuestion = false;
        _pendingQuestionLabel = null;
        _currentStep = targetStep;
      });

      _addAssistantMessage(
        'Perfecto. Volvamos a la pregunta anterior y la cambiamos.',
      );
    }

    await Future.delayed(const Duration(milliseconds: 150));
    await _askCurrentStep();
  }

  String _environmentInterpretation(String context) {
    switch (context) {
      case 'Silencio estable':
        return 'Eso me permite afinar con música más sutil y detallada.';
      case 'Ruido de fondo suave':
        return 'Parece un entorno bastante estable y poco invasivo.';
      case 'Entorno conversacional':
        return 'Detecto un ambiente con actividad hablada o cambios frecuentes.';
      case 'Picos intermitentes':
        return 'Hay interrupciones o sobresaltos acústicos de vez en cuando.';
      case 'Espacio público activo':
        return 'Parece un lugar con bastante actividad alrededor.';
      case 'Ruido continuo intenso':
        return 'El entorno tiene una presencia sonora fuerte y sostenida.';
      case 'Actividad sonora moderada':
        return 'El entorno no está en silencio, pero tampoco parece excesivo.';
      case 'Entorno mixto':
        return 'El entorno tiene una mezcla de estabilidad y cambios puntuales.';
      default:
        return '';
    }
  }

  Future<void> _measureEnvironment({bool fromConversation = false}) async {
    // Analiza el entorno acústico solo si el usuario decide usar esa señal
    // para personalizar la sesión.
    HapticFeedback.lightImpact();
    setState(() {
      isMeasuringNoise = true;
      environmentContext = 'Escuchando...';
    });

    try {
      final profile = await _environmentAudioService.analyzeEnvironment(
        durationSeconds: 5,
      );

      if (!mounted) return;

      setState(() {
        _audioProfile = profile;
        measuredDb = profile.meanDb;
        noiseCategory = profile.noiseCategory;
        environmentContext = profile.environmentContext;
        environmentVariability = profile.stdDev;
        environmentPeakDelta = profile.peakDelta;
        environmentConfidence = profile.confidence;
        _environmentMeasured = true;
        isMeasuringNoise = false;
      });

      debugPrint(
        '[ENV AUDIO] mean=${profile.meanDb.toStringAsFixed(1)} '
        'median=${profile.medianDb.toStringAsFixed(1)} '
        'max=${profile.maxDb.toStringAsFixed(1)} '
        'std=${profile.stdDev.toStringAsFixed(2)} '
        'peakDelta=${profile.peakDelta.toStringAsFixed(1)} '
        'transientRatio=${profile.transientRatio.toStringAsFixed(2)} '
        'bursts=${profile.burstCount} '
        'density=${profile.sampleDensityHz.toStringAsFixed(2)} '
        'stability=${profile.stabilityScore.toStringAsFixed(2)} '
        'category=${profile.noiseCategory} '
        'context=${profile.environmentContext} '
        'confidence=${profile.confidence.toStringAsFixed(2)}',
      );

      if (fromConversation) {
        _addAssistantMessage(_environmentPostMeasurementMessage(profile));
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Entorno actualizado: ${profile.environmentContext} · ${profile.meanDb.toStringAsFixed(1)} dB · ${EnvironmentAudioDecision.fromProfile(profile).statusLabel}',
            ),
          ),
        );
      }
    } catch (e) {
      if (!mounted) return;

      setState(() {
        isMeasuringNoise = false;
        environmentContext = _environmentMeasured
            ? environmentContext
            : 'Sin medir';
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('No he podido analizar el entorno: $e')),
      );
    }
  }

  Future<void> _askCurrentStep() async {
    if (!mounted || _conversationCompleted || _asking) return;
    _asking = true;

    final pendingLabel = _stepQuestionLabel(_currentStep);

    try {
      switch (_currentStep) {
        case 0:
          _addAssistantMessage('¿Cómo vienes hoy?');
          final selected = await showGuidedChoiceSheet<String>(
            context: context,
            title: '¿Cómo vienes hoy?',
            subtitle:
                'Quédate con la opción que más se parezca a cómo estás ahora mismo.',
            options: const [
              GuidedOption(
                value: 'feliz',
                title: 'Con ganas y bastante bien',
                subtitle:
                    'Te notas ligero/a, con buen tono o con ánimo positivo.',
                icon: Icons.wb_sunny_outlined,
              ),
              GuidedOption(
                value: 'neutral',
                title: 'En calma o bastante estable',
                subtitle: 'No estás especialmente arriba ni abajo.',
                icon: Icons.self_improvement_outlined,
              ),
              GuidedOption(
                value: 'estresado',
                title: 'Con la cabeza llena',
                subtitle:
                    'Notas presión, saturación o demasiadas cosas a la vez.',
                icon: Icons.psychology_alt_outlined,
              ),
              GuidedOption(
                value: 'triste',
                title: 'Bajo/a de ánimo',
                subtitle: 'Te apetece algo que te sostenga o te acompañe.',
                icon: Icons.cloud_outlined,
              ),
              GuidedOption(
                value: 'cansado',
                title: 'Agotado/a',
                subtitle: 'Vas justo de energía y te cuesta arrancar.',
                icon: Icons.bedtime_outlined,
              ),
            ],
          );

          if (selected == null) {
            _setPendingQuestion(pendingLabel);
            _addAssistantMessage(
              'No pasa nada. Cuando quieras, retomamos esta pregunta.',
            );
            return;
          }

          _clearPendingQuestion();
          mood = selected;
          _emotionAnswer = _emotionLabel(selected);
          _addUserMessage(_emotionAnswer);
          _addAssistantMessage(
            'Perfecto, ya me sitúo mejor. Así evito proponerte algo que hoy no te pegue nada.',
          );
          _currentStep++;
          break;

        case 1:
          _addAssistantMessage('¿Qué te pide el cuerpo ahora mismo?');
          final selected = await showGuidedChoiceSheet<String>(
            context: context,
            title: '¿Qué te pide el cuerpo ahora mismo?',
            subtitle:
                'Prefiero quedarme con lo que necesitas ahora antes que con una etiqueta.',
            options: const [
              GuidedOption(
                value: 'foco',
                title: 'Concentrarme y poner orden',
                subtitle: 'Quiero claridad mental y menos distracción.',
                icon: Icons.center_focus_strong_outlined,
              ),
              GuidedOption(
                value: 'relajacion',
                title: 'Bajar revoluciones',
                subtitle: 'Necesito soltar tensión y respirar un poco.',
                icon: Icons.spa_outlined,
              ),
              GuidedOption(
                value: 'energia',
                title: 'Recuperar impulso',
                subtitle: 'Quiero activarme, moverme o subir el ánimo.',
                icon: Icons.bolt_outlined,
              ),
            ],
          );

          if (selected == null) {
            _setPendingQuestion(pendingLabel);
            _addAssistantMessage(
              'No pasa nada. Cuando quieras, retomamos esta pregunta.',
            );
            return;
          }

          _clearPendingQuestion();
          goal = selected;
          _goalAnswer = _goalLabel(selected);
          _addUserMessage(_goalAnswer);
          _addAssistantMessage(
            'Vale, me quedo con eso. Voy a orientar la sesión hacia lo que más sentido tenga para ti ahora.',
          );
          _currentStep++;
          break;

        case 2:
          _addAssistantMessage('¿Cómo vas de energía ahora mismo?');
          final selected = await showGuidedChoiceSheet<int>(
            context: context,
            title: '¿Cómo vas de energía ahora mismo?',
            subtitle:
                'Piensa en cómo estás de pila, sin buscar precisión milimétrica.',
            options: const [
              GuidedOption(
                value: 1,
                title: 'Muy baja',
                subtitle: 'Me cuesta arrancar.',
                icon: Icons.battery_0_bar_outlined,
              ),
              GuidedOption(
                value: 2,
                title: 'Baja',
                subtitle: 'Voy algo cansado/a.',
                icon: Icons.battery_2_bar_outlined,
              ),
              GuidedOption(
                value: 3,
                title: 'Media',
                subtitle: 'Estoy normal, sin destacar mucho.',
                icon: Icons.battery_4_bar_outlined,
              ),
              GuidedOption(
                value: 4,
                title: 'Alta',
                subtitle: 'Tengo bastante empuje.',
                icon: Icons.battery_5_bar_outlined,
              ),
              GuidedOption(
                value: 5,
                title: 'Muy alta',
                subtitle: 'Voy con mucha energía.',
                icon: Icons.flash_on_outlined,
              ),
            ],
          );

          if (selected == null) {
            _setPendingQuestion(pendingLabel);
            _addAssistantMessage(
              'No pasa nada. Cuando quieras, retomamos esta pregunta.',
            );
            return;
          }

          _clearPendingQuestion();
          energyLevel = selected.toDouble();
          _energyAnswer = _energyLabel(selected);
          _addUserMessage(_energyAnswer);
          _addAssistantMessage(
            'Genial. Así ajusto mejor cuánto tirar o cuánto acompañar.',
          );
          _currentStep++;
          break;

        case 3:
          _addAssistantMessage('¿Cómo notas la cabeza hoy?');
          final selected = await showGuidedChoiceSheet<int>(
            context: context,
            title: '¿Cómo notas la cabeza hoy?',
            subtitle:
                'No busco un dato exacto, solo una foto rápida del momento.',
            options: const [
              GuidedOption(
                value: 1,
                title: 'Muy bajo',
                subtitle: 'Me siento bastante suelto/a.',
                icon: Icons.sentiment_very_satisfied_outlined,
              ),
              GuidedOption(
                value: 2,
                title: 'Bajo',
                subtitle: 'Estoy bastante bien.',
                icon: Icons.sentiment_satisfied_outlined,
              ),
              GuidedOption(
                value: 3,
                title: 'Medio',
                subtitle: 'Hay algo de tensión, pero la llevo.',
                icon: Icons.sentiment_neutral_outlined,
              ),
              GuidedOption(
                value: 4,
                title: 'Alto',
                subtitle: 'Voy cargado/a.',
                icon: Icons.sentiment_dissatisfied_outlined,
              ),
              GuidedOption(
                value: 5,
                title: 'Muy alto',
                subtitle: 'Estoy realmente saturado/a.',
                icon: Icons.warning_amber_outlined,
              ),
            ],
          );

          if (selected == null) {
            _setPendingQuestion(pendingLabel);
            _addAssistantMessage(
              'No pasa nada. Cuando quieras, retomamos esta pregunta.',
            );
            return;
          }

          _clearPendingQuestion();
          stressLevel = selected.toDouble();
          _stressAnswer = _stressLabel(selected);
          _addUserMessage(_stressAnswer);
          _addAssistantMessage(
            'Entendido. Así puedo medir mejor si hoy conviene empujar o bajar un poco el ruido mental.',
          );
          _currentStep++;
          break;

        case 4:
          _addAssistantMessage('¿Qué tipo de música te entra mejor ahora?');
          final selected = await showGuidedChoiceSheet<String>(
            context: context,
            title: '¿Qué tipo de música te entra mejor ahora?',
            subtitle:
                'Puedo ir a algo más limpio o a algo más acompañado, según te apetezca.',
            options: const [
              GuidedOption(
                value: 'instrumental',
                title: 'Algo instrumental',
                subtitle: 'Sin voz, más limpio y espacioso.',
                icon: Icons.piano_outlined,
              ),
              GuidedOption(
                value: 'indistinto',
                title: 'Me da igual',
                subtitle: 'Lo importante es que encaje conmigo ahora.',
                icon: Icons.tune_outlined,
              ),
              GuidedOption(
                value: 'con_voz',
                title: 'Con voz',
                subtitle:
                    'Me apetece sentirme acompañado/a por letras o voces.',
                icon: Icons.mic_outlined,
              ),
            ],
          );

          if (selected == null) {
            _setPendingQuestion(pendingLabel);
            _addAssistantMessage(
              'No pasa nada. Cuando quieras, retomamos esta pregunta.',
            );
            return;
          }

          _clearPendingQuestion();
          vocalPreference = selected;
          _voiceAnswer = _voiceLabel(selected);
          _addUserMessage(_voiceAnswer);
          _addAssistantMessage(
            'Perfecto. Así la sesión se sentirá más tuya y menos impuesta.',
          );
          _currentStep++;
          break;

        case 5:
          _addAssistantMessage('¿Con cuánta intensidad te apetece la música?');
          final selected = await showGuidedChoiceSheet<String>(
            context: context,
            title: '¿Con cuánta intensidad te apetece la música?',
            subtitle:
                'Puedo llevarte a algo muy suave o a algo con más empuje, según te pida el momento.',
            options: const [
              GuidedOption(
                value: 'suave',
                title: 'Suave',
                subtitle: 'Más delicado, menos invasivo.',
                icon: Icons.water_drop_outlined,
              ),
              GuidedOption(
                value: 'media',
                title: 'Media',
                subtitle: 'Equilibrado, sin pasarse.',
                icon: Icons.waves_outlined,
              ),
              GuidedOption(
                value: 'alta',
                title: 'Alta',
                subtitle: 'Con presencia, ritmo o fuerza.',
                icon: Icons.graphic_eq_outlined,
              ),
            ],
          );

          if (selected == null) {
            _setPendingQuestion(pendingLabel);
            _addAssistantMessage(
              'No pasa nada. Cuando quieras, retomamos esta pregunta.',
            );
            return;
          }

          _clearPendingQuestion();
          intensityPreference = selected;
          _intensityAnswer = _intensityLabel(selected);
          _addUserMessage(_intensityAnswer);
          _addAssistantMessage(
            'Bien. Así no solo elijo qué suena, sino cómo quieres que te llegue.',
          );
          _currentStep++;
          break;

        case 6:
          _addAssistantMessage(
            '¿Hoy quieres que me apoye más en lo que he aprendido de ti o que abra un poco el radar?',
          );
          final selected = await showGuidedChoiceSheet<String>(
            context: context,
            title:
                '¿Hoy quieres que me apoye más en lo que he aprendido de ti o que abra un poco el radar?',
            subtitle:
                'Aquí ajusto cuánto peso doy a tus patrones aprendidos a partir de sesiones y feedback anteriores.',
            options: const [
              GuidedOption(
                value: 'familiar',
                title: 'Apóyate en lo aprendido',
                subtitle: 'Confía más en lo que suele funcionarme.',
                icon: Icons.home_outlined,
              ),
              GuidedOption(
                value: 'equilibrado',
                title: 'Un punto medio',
                subtitle: 'Combina lo aprendido conmigo con algo de aire fresco.',
                icon: Icons.balance_outlined,
              ),
              GuidedOption(
                value: 'descubrir',
                title: 'Abre un poco el radar',
                subtitle: 'Deja más margen para salir de mis patrones previos.',
                icon: Icons.travel_explore_outlined,
              ),
            ],
          );

          if (selected == null) {
            _setPendingQuestion(pendingLabel);
            _addAssistantMessage(
              'No pasa nada. Cuando quieras, retomamos esta pregunta.',
            );
            return;
          }

          _clearPendingQuestion();
          explorationPreference = selected;
          _explorationAnswer = _explorationLabel(selected);
          _addUserMessage(_explorationAnswer);
          _addAssistantMessage(
            'Me sirve mucho. Así calibro cuánto confiar en lo que he ido aprendiendo de tus gustos y cuánto dejar espacio a salir de ahí.',
          );
          _currentStep++;
          break;

        case 7:
          _addAssistantMessage(
            '¿Te tira más algo conocido o algo menos obvio?',
          );
          final selected = await showGuidedChoiceSheet<String>(
            context: context,
            title: '¿Te tira más algo conocido o algo menos obvio?',
            subtitle: 'Aquí ajusto el tipo de catálogo que más te apetece hoy.',
            options: const [
              GuidedOption(
                value: 'mainstream',
                title: 'Más conocido',
                subtitle: 'Algo directo y reconocible.',
                icon: Icons.local_fire_department_outlined,
              ),
              GuidedOption(
                value: 'mixta',
                title: 'Un punto medio',
                subtitle: 'Ni muy obvio ni muy de nicho.',
                icon: Icons.auto_awesome_outlined,
              ),
              GuidedOption(
                value: 'alternativa',
                title: 'Más alternativa',
                subtitle: 'Algo menos evidente o más especial.',
                icon: Icons.nightlight_round_outlined,
              ),
            ],
          );

          if (selected == null) {
            _setPendingQuestion(pendingLabel);
            _addAssistantMessage(
              'No pasa nada. Cuando quieras, retomamos esta pregunta.',
            );
            return;
          }

          _clearPendingQuestion();
          popularityPreference = selected;
          _popularityAnswer = _popularityLabel(selected);
          _addUserMessage(_popularityAnswer);
          _addAssistantMessage(
            'Perfecto. Así afino no solo la emoción, sino también el tipo de hallazgo.',
          );
          _currentStep++;
          break;

        case 8:
          _addAssistantMessage(
            '¿Cuánto rato quieres que esté contigo esta sesión?',
          );
          final selected = await showGuidedChoiceSheet<int>(
            context: context,
            title: '¿Cuánto rato quieres que esté contigo esta sesión?',
            subtitle: 'Solo para darle un tamaño realista a la sesión.',
            options: const [
              GuidedOption(
                value: 15,
                title: '15 minutos',
                subtitle: 'Una cápsula breve.',
                icon: Icons.timelapse_outlined,
              ),
              GuidedOption(
                value: 20,
                title: '20 minutos',
                subtitle: 'Para resetear un poco.',
                icon: Icons.schedule_outlined,
              ),
              GuidedOption(
                value: 30,
                title: '30 minutos',
                subtitle: 'Una sesión con más recorrido.',
                icon: Icons.av_timer_outlined,
              ),
              GuidedOption(
                value: 40,
                title: '40 minutos',
                subtitle: 'Quiero que me acompañe más tiempo.',
                icon: Icons.hourglass_bottom_outlined,
              ),
            ],
          );

          if (selected == null) {
            _setPendingQuestion(pendingLabel);
            _addAssistantMessage(
              'No pasa nada. Cuando quieras, retomamos esta pregunta.',
            );
            return;
          }

          _clearPendingQuestion();
          sessionDurationMin = selected.toDouble();
          _durationAnswer = '$selected minutos';
          _addUserMessage(_durationAnswer);
          _addAssistantMessage('Perfecto. Ya casi está.');
          _currentStep++;
          break;

        case 9:
          _addAssistantMessage(
            'Si esta sesión te sentara bien, ¿cómo te gustaría acabar?',
          );
          final selected = await showGuidedChoiceSheet<String>(
            context: context,
            title: 'Si esta sesión te sentara bien, ¿cómo te gustaría acabar?',
            subtitle:
                'No hace falta que sea perfecto. Solo dime un poco hacia dónde te gustaría moverte.',
            options: const [
              GuidedOption(
                value: 'mas_ligero',
                title: 'Más ligero/a',
                subtitle: 'Con menos peso mental o emocional.',
                icon: Icons.air_outlined,
              ),
              GuidedOption(
                value: 'mas_centrado',
                title: 'Más centrado/a',
                subtitle: 'Con más claridad y sensación de orden.',
                icon: Icons.filter_center_focus_outlined,
              ),
              GuidedOption(
                value: 'mas_acompanado',
                title: 'Más acompañado/a',
                subtitle: 'Con una sensación de sostén o compañía.',
                icon: Icons.favorite_outline,
              ),
              GuidedOption(
                value: 'mas_despierto',
                title: 'Más despierto/a',
                subtitle: 'Con más activación o impulso.',
                icon: Icons.bolt_outlined,
              ),
              GuidedOption(
                value: 'mas_calmado',
                title: 'Más calmado/a',
                subtitle: 'Con menos tensión y más espacio interno.',
                icon: Icons.spa_outlined,
              ),
            ],
          );

          if (selected == null) {
            _setPendingQuestion(pendingLabel);
            _addAssistantMessage(
              'No pasa nada. Cuando quieras, retomamos esta pregunta.',
            );
            return;
          }

          _clearPendingQuestion();
          desiredOutcome = selected;
          _desiredOutcomeAnswer = _desiredOutcomeLabel(selected);
          _addUserMessage(_desiredOutcomeAnswer);
          _addAssistantMessage(
            'Eso me viene genial, porque así no me quedo solo con cómo vienes, sino también con hacia dónde quieres ir.',
          );
          _currentStep++;
          break;

        case 10:
          _addAssistantMessage(
            '¿Quieres que tenga en cuenta también lo que tienes alrededor ahora mismo?',
          );
          final selected = await showGuidedChoiceSheet<bool>(
            context: context,
            title:
                '¿Quieres que tenga en cuenta también lo que tienes alrededor?',
            subtitle:
                'Puedo escuchar unos segundos el ambiente para afinar mejor la recomendación, si te viene bien.',
            options: const [
              GuidedOption(
                value: true,
                title: 'Sí, escúchalo',
                subtitle: 'Usa mi entorno como una pista más.',
                icon: Icons.hearing_outlined,
              ),
              GuidedOption(
                value: false,
                title: 'Prefiero saltarlo',
                subtitle: 'Quédate solo con lo que me has contado.',
                icon: Icons.not_interested_outlined,
              ),
            ],
          );

          if (selected == null) {
            _setPendingQuestion(pendingLabel);
            _addAssistantMessage(
              'No pasa nada. Cuando quieras, retomamos esta pregunta.',
            );
            return;
          }

          _clearPendingQuestion();
          _addUserMessage(
            selected ? 'Sí, ten en cuenta mi entorno' : 'Prefiero saltarlo',
          );

          if (selected) {
            _addAssistantMessage('Perfecto, escucho un momento.');
            await _measureEnvironment(fromConversation: true);
          } else {
            setState(_clearEnvironmentMeasurement);
            _addAssistantMessage(
              'Perfecto. Me quedo solo con lo que me has contado.',
            );
          }

          _currentStep++;
          await _finishConversation();
          break;
      }
    } finally {
      _asking = false;
    }

    if (!_conversationCompleted && mounted) {
      await Future.delayed(const Duration(milliseconds: 250));
      await _askCurrentStep();
    }
  }

  String _buildEmotionalReflection() {
    final stress = stressLevel.toInt();
    final energy = energyLevel.toInt();

    if (mood == 'estresado' && goal == 'relajacion') {
      if (energy <= 2) {
        return 'Ahora mismo te noto bastante cargado/a y con poca energía. Voy a intentar que la sesión te dé espacio, baje tensión y no te exija más de la cuenta.';
      }
      return 'Te noto con bastante presión encima. Voy a buscar algo que te ayude a aflojar sin dejarte fuera de sitio.';
    }

    if (mood == 'feliz' && goal == 'energia') {
      return 'Te noto con buen tono y bastante disposición. Voy a acompañar esa energía con algo que sume sin pasarse de rosca.';
    }

    if (mood == 'neutral' && goal == 'foco') {
      return 'Te noto bastante estable, y eso es un buen punto de partida. Voy a buscar una sesión que te ayude a centrarte sin invadir demasiado.';
    }

    if (mood == 'cansado' && goal == 'energia') {
      return 'Te noto cansado/a, así que no voy a tirar de algo agresivo. Buscaré una sesión que te reactive poco a poco y con tacto.';
    }

    if (mood == 'triste' && goal == 'relajacion') {
      return 'Te noto más sensible o apagado/a. Voy a intentar construir una sesión que acompañe, sostenga y no se sienta invasiva.';
    }

    if (stress >= 4 && energy >= 4) {
      return 'Te noto bastante activado/a ahora mismo. Voy a cuidar que la música tenga presencia, pero sin echar más leña al fuego.';
    }

    if (stress >= 4 && energy <= 2) {
      return 'Veo una mezcla de tensión alta y poca energía. Intentaré darte una sesión que te recoja más de lo que te exija.';
    }

    if (energy >= 4 && goal == 'foco') {
      return 'Tienes bastante energía, así que voy a intentar canalizarla hacia algo útil y estable, no hacia algo que te disperse.';
    }

    if (goal == 'relajacion') {
      return 'Voy a priorizar una sensación de calma, espacio y menos fricción por dentro.';
    }

    if (goal == 'energia') {
      return 'Voy a priorizar una sensación de impulso y de recuperar ritmo, pero ajustada a cómo vienes.';
    }

    return 'Ya tengo una imagen bastante clara del momento. Voy a buscar una sesión que encaje contigo sin forzar nada.';
  }

  String _buildPlaylistIntent() {
    final voiceText = switch (vocalPreference) {
      'instrumental' => 'más instrumental',
      'con_voz' => 'con más presencia de voz',
      _ => 'equilibrada en lo vocal',
    };

    final intensityText = switch (intensityPreference) {
      'suave' => 'suave y poco invasiva',
      'alta' => 'con más empuje y presencia',
      _ => 'con una intensidad equilibrada',
    };

    final discoveryText = switch (explorationPreference) {
      'familiar' => 'apoyándome más en lo que he aprendido de ti',
      'descubrir' => 'dejando más margen para salir de tus patrones previos',
      _ => 'mezclando lo aprendido contigo con algo de aire fresco',
    };

    final popularityText = switch (popularityPreference) {
      'mainstream' => 'más cercana a lo conocido',
      'alternativa' => 'algo más alternativa',
      _ => 'en un punto medio de catálogo',
    };

    final outcomeText = switch (desiredOutcome) {
      'mas_ligero' => 'con la intención de dejarte algo más ligero/a',
      'mas_centrado' =>
        'con la intención de ayudarte a sentirte más centrado/a',
      'mas_acompanado' => 'con la intención de que te sientas más acompañado/a',
      'mas_despierto' => 'con la intención de dejarte más despierto/a',
      'mas_calmado' => 'con la intención de dejarte más calmado/a',
      _ => 'intentando acompañar bien este momento',
    };

    return 'Voy a prepararte una sesión $intensityText, $voiceText, $popularityText y $discoveryText, $outcomeText.';
  }

  Future<void> _finishConversation() async {
    // Cierra la entrevista mostrando un resumen emocional antes de pedir la
    // recomendación al backend.
    setState(() {
      _conversationCompleted = true;
    });

    _addAssistantMessage(_buildEmotionalReflection());
    _addAssistantMessage(_buildPlaylistIntent());

    if (_environmentMeasured) {
      _addAssistantMessage(
        _useEnvironmentForPersonalization
            ? 'Además, usaré la escucha del entorno como una pista más para ajustar la recomendación.'
            : 'Además, he medido tu entorno, pero hoy lo dejaré solo como contexto informativo para no forzar la personalización con una lectura poco sólida.',
      );
    } else {
      _addAssistantMessage(
        'Esta vez me apoyaré sobre todo en lo que me has contado, sin meter el entorno en la ecuación.',
      );
    }

    _addAssistantMessage('Si te cuadra, te preparo ya la recomendación.');
  }

  Future<void> _restartConversation() async {
    HapticFeedback.selectionClick();
    setState(() {
      _messages.clear();
      _started = false;
      _conversationCompleted = false;
      _asking = false;
      _currentStep = 0;

      mood = 'neutral';
      goal = 'foco';
      stressLevel = 3;
      energyLevel = 3;
      vocalPreference = 'indistinto';
      intensityPreference = 'media';
      explorationPreference = 'equilibrado';
      popularityPreference = 'mixta';
      sessionDurationMin = 20;
      desiredOutcome = 'mas_calmado';

      _clearEnvironmentMeasurement();

      _hasPendingQuestion = false;
      _pendingQuestionLabel = null;

      _emotionAnswer = '';
      _goalAnswer = '';
      _energyAnswer = '';
      _stressAnswer = '';
      _voiceAnswer = '';
      _intensityAnswer = '';
      _explorationAnswer = '';
      _popularityAnswer = '';
      _durationAnswer = '';
      _desiredOutcomeAnswer = '';
    });

    await _bootConversation();
  }

  Future<void> _submit() async {
    // Encadena check-in backend, persistencia en Firestore, generación de la
    // recomendación y navegación a la siguiente pantalla.
    HapticFeedback.mediumImpact();
    setState(() => isLoading = true);
    bool loadingRouteShown = false;
    bool loadingRouteDismissed = false;

    if (mounted) {
      Navigator.push(
        context,
        buildHarmonyRoute(const RecommendationLoadingScreen()),
      );
      loadingRouteShown = true;
    }

    try {
      await _checkinService.createCheckin(
        mood: mood,
        goal: goal,
        stressLevel: stressLevel.toInt(),
        energyLevel: energyLevel.toInt(),
        noiseCategory: _backendNoiseCategory,
      );

      final profileToSave =
          _audioProfile ??
          EnvironmentAudioProfile.fallback(
            noiseCategory: _displayNoiseCategory,
            environmentContext: environmentContext,
            measuredDb: measuredDb,
          );

      await _checkinFirestoreService.saveCheckin(
        mood: mood,
        goal: goal,
        stressLevel: stressLevel.toInt(),
        energyLevel: energyLevel.toInt(),
        audioProfile: profileToSave,
        desiredOutcome: desiredOutcome,
      );

      final recommendation = await _recommendationService
          .generateRecommendation(
            mood: mood,
            goal: goal,
            stressLevel: stressLevel.toInt(),
            energyLevel: energyLevel.toInt(),
            noiseCategory: _backendNoiseCategory,
            vocalPreference: vocalPreference,
            intensityPreference: intensityPreference,
            explorationPreference: explorationPreference,
            popularityPreference: popularityPreference,
            sessionDurationMin: sessionDurationMin.toInt(),
            desiredOutcome: desiredOutcome,
            useEnvironment: _useEnvironmentForPersonalization,
            environmentContext: _useEnvironmentForPersonalization
                ? environmentContext
                : null,
            environmentVariability: _useEnvironmentForPersonalization
                ? environmentVariability
                : null,
            environmentPeakDelta: _useEnvironmentForPersonalization
                ? environmentPeakDelta
                : null,
            environmentConfidence: _useEnvironmentForPersonalization
                ? environmentConfidence
                : null,
            transientRatio: _useEnvironmentForPersonalization
                ? _audioProfile?.transientRatio
                : null,
            burstCount: _useEnvironmentForPersonalization
                ? _audioProfile?.burstCount
                : null,
          );

      await _recommendationFirestoreService.saveRecommendation(
        recommendation: recommendation,
        mood: mood,
        goal: goal,
        stressLevel: stressLevel.toInt(),
        energyLevel: energyLevel.toInt(),
        noiseCategory: _displayNoiseCategory,
        vocalPreference: vocalPreference,
        intensityPreference: intensityPreference,
        explorationPreference: explorationPreference,
        popularityPreference: popularityPreference,
        sessionDurationMin: sessionDurationMin.toInt(),
        desiredOutcome: desiredOutcome,
        spotifyUserId: SpotifySession.instance.profile?['id']?.toString(),
        useEnvironment: _useEnvironmentForPersonalization,
        environmentMeasured: _environmentMeasured,
        environmentContext: environmentContext,
        environmentConfidence: environmentConfidence,
        environmentStabilityScore: _audioProfile?.stabilityScore,
        environmentSampleDensityHz: _audioProfile?.sampleDensityHz,
        environmentUsageStatus: _environmentUsageBadge,
        environmentUsageRationale: _environmentUsageRationale,
      );

      if (!mounted) return;

      if (loadingRouteShown && Navigator.of(context).canPop()) {
        Navigator.of(context).pop();
        loadingRouteDismissed = true;
      }

      Navigator.push(
        context,
        buildHarmonyRoute(
          RecommendationScreen(
            recommendation: recommendation,
            goal: goal,
            mood: mood,
            stressLevel: stressLevel.toInt(),
            energyLevel: energyLevel.toInt(),
            noiseCategory: _displayNoiseCategory,
            vocalPreference: vocalPreference,
            intensityPreference: intensityPreference,
            explorationPreference: explorationPreference,
            popularityPreference: popularityPreference,
            sessionDurationMin: sessionDurationMin.toInt(),
            desiredOutcome: desiredOutcome,
            useEnvironment: _useEnvironmentForPersonalization,
            environmentContext: _useEnvironmentForPersonalization
                ? environmentContext
                : null,
            environmentVariability: _useEnvironmentForPersonalization
                ? environmentVariability
                : null,
            environmentPeakDelta: _useEnvironmentForPersonalization
                ? environmentPeakDelta
                : null,
            environmentConfidence: _useEnvironmentForPersonalization
                ? environmentConfidence
                : null,
            transientRatio: _useEnvironmentForPersonalization
                ? _audioProfile?.transientRatio
                : null,
            burstCount: _useEnvironmentForPersonalization
                ? _audioProfile?.burstCount
                : null,
            environmentMeasured: _environmentMeasured,
            environmentUsageStatus: _environmentUsageBadge,
            environmentUsageRationale: _environmentUsageRationale,
            environmentStabilityScore: _audioProfile?.stabilityScore,
            environmentSampleDensityHz: _audioProfile?.sampleDensityHz,
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      if (loadingRouteShown &&
          !loadingRouteDismissed &&
          Navigator.of(context).canPop()) {
        Navigator.of(context).pop();
        loadingRouteDismissed = true;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('No he podido generar la recomendación: $e')),
      );
    } finally {
      if (mounted) {
        setState(() => isLoading = false);
      }
    }
  }

  String _emotionLabel(String value) {
    switch (value) {
      case 'feliz':
        return 'Con ganas y bastante bien';
      case 'neutral':
        return 'En calma o estable';
      case 'estresado':
        return 'Con la cabeza llena';
      case 'triste':
        return 'Bajo/a de ánimo';
      case 'cansado':
        return 'Agotado/a';
      default:
        return value;
    }
  }

  String _goalLabel(String value) {
    switch (value) {
      case 'foco':
        return 'Concentrarme y poner orden';
      case 'relajacion':
        return 'Bajar revoluciones';
      case 'energia':
        return 'Recuperar impulso';
      default:
        return value;
    }
  }

  String _energyLabel(int value) {
    switch (value) {
      case 1:
        return 'Muy baja';
      case 2:
        return 'Baja';
      case 3:
        return 'Media';
      case 4:
        return 'Alta';
      case 5:
        return 'Muy alta';
      default:
        return value.toString();
    }
  }

  String _stressLabel(int value) {
    switch (value) {
      case 1:
        return 'Muy bajo';
      case 2:
        return 'Bajo';
      case 3:
        return 'Medio';
      case 4:
        return 'Alto';
      case 5:
        return 'Muy alto';
      default:
        return value.toString();
    }
  }

  String _voiceLabel(String value) {
    switch (value) {
      case 'instrumental':
        return 'Algo instrumental';
      case 'indistinto':
        return 'Me da igual';
      case 'con_voz':
        return 'Con voz';
      default:
        return value;
    }
  }

  String _intensityLabel(String value) {
    switch (value) {
      case 'suave':
        return 'Suave';
      case 'media':
        return 'Media';
      case 'alta':
        return 'Alta';
      default:
        return value;
    }
  }

  String _explorationLabel(String value) {
    switch (value) {
      case 'familiar':
        return 'Apóyate en lo aprendido';
      case 'equilibrado':
        return 'Un punto medio';
      case 'descubrir':
        return 'Abre un poco el radar';
      default:
        return value;
    }
  }

  String _popularityLabel(String value) {
    switch (value) {
      case 'mainstream':
        return 'Más conocido';
      case 'mixta':
        return 'Un punto medio';
      case 'alternativa':
        return 'Más alternativa';
      default:
        return value;
    }
  }

  String _desiredOutcomeLabel(String value) {
    switch (value) {
      case 'mas_ligero':
        return 'Más ligero/a';
      case 'mas_centrado':
        return 'Más centrado/a';
      case 'mas_acompanado':
        return 'Más acompañado/a';
      case 'mas_despierto':
        return 'Más despierto/a';
      case 'mas_calmado':
        return 'Más calmado/a';
      default:
        return value;
    }
  }

  Widget _chatBubble(_ChatMessage message) {
    final theme = Theme.of(context);
    final isUser = message.isUser;

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 310),
        margin: EdgeInsets.only(left: isUser ? 46 : 0, right: isUser ? 0 : 46),
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
        decoration: BoxDecoration(
          gradient: isUser
              ? const LinearGradient(
                  colors: [Color(0xFF1E4B43), Color(0xFF2B645A)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                )
              : const LinearGradient(
                  colors: [Color(0xFFFFFCF8), Color(0xFFF8F1E7)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
          border: Border.all(
            color: isUser ? Colors.transparent : const Color(0xFFE8DCCD),
          ),
          boxShadow: const [
            BoxShadow(
              color: Color(0x101F2421),
              blurRadius: 18,
              offset: Offset(0, 10),
            ),
          ],
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(26),
            topRight: const Radius.circular(26),
            bottomLeft: Radius.circular(isUser ? 26 : 10),
            bottomRight: Radius.circular(isUser ? 10 : 26),
          ),
        ),
        child: Text(
          message.text,
          style: TextStyle(
            color: isUser
                ? theme.colorScheme.onPrimary
                : theme.colorScheme.onSurface,
            fontSize: 15,
            height: 1.45,
            fontWeight: isUser ? FontWeight.w600 : FontWeight.w500,
          ),
        ),
      ),
    );
  }

  Widget _summaryChip(String label, String value, IconData icon) {
    return Container(
      constraints: const BoxConstraints(minWidth: 150),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(22),
        gradient: const LinearGradient(
          colors: [Color(0xFFFFFCF8), Color(0xFFF7EFE5)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        border: Border.all(color: const Color(0xFFE7DCCD)),
        boxShadow: const [
          BoxShadow(
            color: Color(0x0A1F2421),
            blurRadius: 14,
            offset: Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 28,
                height: 28,
                decoration: BoxDecoration(
                  color: const Color(0xFFE9F0EB),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, size: 16, color: const Color(0xFF1E4B43)),
              ),
              const SizedBox(width: 8),
              Flexible(
                child: Text(
                  label,
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFF6D655E),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            value,
            style: const TextStyle(
              fontWeight: FontWeight.w700,
              color: Color(0xFF1F2421),
              height: 1.25,
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _environmentAudioService.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final currentPrompt = switch (_currentStep) {
      0 => 'Responder cómo llegas hoy',
      1 => 'Responder qué necesitas',
      2 => 'Responder nivel de energía',
      3 => 'Responder nivel de tensión',
      4 => 'Responder tipo de escucha',
      5 => 'Responder intensidad',
      6 => 'Responder exploración',
      7 => 'Responder estilo de catálogo',
      8 => 'Responder duración',
      9 => 'Responder cómo te gustaría terminar',
      10 => 'Responder sobre el entorno',
      _ => 'Continuar',
    };
    final answeredSteps = _conversationCompleted
        ? 11
        : (_currentStep + (_hasPendingQuestion ? 0 : 0)).clamp(0, 11);
    final progressValue = _conversationCompleted
        ? 1.0
        : ((_currentStep) / 11).clamp(0, 1).toDouble();
    final progressText = _conversationCompleted
        ? 'Conversación cerrada'
        : '${answeredSteps.clamp(0, 10)}/10 respuestas';
    final environmentStatusText = !_environmentMeasured
        ? 'Sin escucha'
        : _useEnvironmentForPersonalization
        ? 'Entorno activo'
        : 'Entorno prudente';

    final isCompactCheckinLayout =
        MediaQuery.sizeOf(context).height < 820 ||
        MediaQuery.sizeOf(context).width < 390;

    final bottomActionBar = SafeArea(
      top: false,
      child: Container(
        padding: EdgeInsets.fromLTRB(
          16,
          isCompactCheckinLayout ? 8 : 10,
          16,
          isCompactCheckinLayout ? 12 : 16,
        ),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFFFFFCF8), Color(0xFFF7EFE4)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
          borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
          boxShadow: [
            BoxShadow(
              blurRadius: 24,
              color: Colors.black.withValues(alpha: 0.07),
              offset: const Offset(0, -6),
            ),
          ],
        ),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (!_conversationCompleted) ...[
                FilledButton.icon(
                  onPressed: _asking ? null : _askCurrentStep,
                  icon: const Icon(Icons.chat_bubble_outline),
                  label: Text(
                    _hasPendingQuestion
                        ? 'Seguir por donde lo dejamos'
                        : currentPrompt,
                  ),
                ),
                if (_canGoBackOneStep) ...[
                  SizedBox(height: isCompactCheckinLayout ? 6 : 8),
                  OutlinedButton.icon(
                    onPressed: _goBackOneStep,
                    icon: const Icon(Icons.arrow_back),
                    label: const Text('Cambiar respuesta anterior'),
                  ),
                ],
              ] else ...[
                FilledButton(
                  onPressed: isLoading ? null : _submit,
                  child: isLoading
                      ? const SizedBox(
                          width: 22,
                          height: 22,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Generar recomendación'),
                ),
                SizedBox(height: isCompactCheckinLayout ? 8 : 10),
                OutlinedButton.icon(
                  onPressed: isMeasuringNoise
                      ? null
                      : () => _measureEnvironment(fromConversation: false),
                  icon: isMeasuringNoise
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.mic),
                  label: Text(
                    isMeasuringNoise
                        ? 'Analizando entorno...'
                        : _environmentMeasured
                        ? 'Volver a analizar el entorno'
                        : 'Analizar el entorno',
                  ),
                ),
                SizedBox(height: isCompactCheckinLayout ? 4 : 8),
                TextButton.icon(
                  onPressed: _canGoBackOneStep ? _goBackOneStep : null,
                  icon: const Icon(Icons.edit_outlined),
                  label: const Text('Cambiar última respuesta'),
                ),
                const SizedBox(height: 2),
                TextButton(
                  onPressed: _restartConversation,
                  child: const Text('Rehacer conversación'),
                ),
              ],
            ],
          ),
        ),
      ),
    );

    return Scaffold(
      bottomNavigationBar: bottomActionBar,
      body: LayoutBuilder(
        builder: (context, constraints) {
          final isCompactLayout =
              constraints.maxHeight < 820 || constraints.maxWidth < 390;
          final heroTitleSize = isCompactLayout ? 28.0 : 34.0;
          final heroBodySize = isCompactLayout ? 14.0 : 15.0;
          final heroTopPadding = isCompactLayout ? 18.0 : 20.0;
          final heroBottomPadding = isCompactLayout ? 18.0 : 22.0;

          return DecoratedBox(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  Color(0xFFF8F1E8),
                  Color(0xFFF0E6DA),
                  Color(0xFFE8EEE7),
                ],
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
              ),
            ),
            child: Column(
              children: [
            SafeArea(
              bottom: false,
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 18, 20, 0),
                child: Container(
                  clipBehavior: Clip.antiAlias,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(40),
                    gradient: const LinearGradient(
                      colors: [
                        Color(0xFF122E2A),
                        Color(0xFF214A43),
                        Color(0xFF35655D),
                        Color(0xFFC37D58),
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x22000000),
                        blurRadius: 26,
                        offset: Offset(0, 16),
                      ),
                    ],
                  ),
                  child: Stack(
                    children: [
                      Positioned(
                        top: -18,
                        right: -14,
                        child: Container(
                          width: 130,
                          height: 130,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: Colors.white.withValues(alpha: 0.08),
                          ),
                        ),
                      ),
                      Positioned(
                        bottom: -32,
                        left: -12,
                        child: Container(
                          width: 118,
                          height: 118,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: Colors.white.withValues(alpha: 0.06),
                          ),
                        ),
                      ),
                      Padding(
                        padding: EdgeInsets.fromLTRB(
                          20,
                          heroTopPadding,
                          20,
                          heroBottomPadding,
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Container(
                                  decoration: BoxDecoration(
                                    color: Colors.white.withValues(alpha: 0.12),
                                    borderRadius: BorderRadius.circular(18),
                                  ),
                                  child: IconButton(
                                    onPressed: () =>
                                        Navigator.of(context).maybePop(),
                                    icon: const Icon(
                                      Icons.arrow_back_rounded,
                                      color: Colors.white,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 10),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 12,
                                    vertical: 8,
                                  ),
                                  decoration: BoxDecoration(
                                    color: Colors.white.withValues(alpha: 0.12),
                                    borderRadius: BorderRadius.circular(999),
                                    border: Border.all(
                                      color: Colors.white.withValues(
                                        alpha: 0.08,
                                      ),
                                    ),
                                  ),
                                  child: const Text(
                                    'CHECK-IN',
                                    style: TextStyle(
                                      color: Colors.white,
                                      fontSize: 11,
                                      letterSpacing: 1.4,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                ),
                                const Spacer(),
                                Container(
                                  decoration: BoxDecoration(
                                    color: Colors.white.withValues(alpha: 0.12),
                                    borderRadius: BorderRadius.circular(18),
                                  ),
                                  child: const Padding(
                                    padding: EdgeInsets.all(2),
                                    child: HomeShortcutButton(),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 20),
                            Text(
                              'Tu momento entra aquí y sale convertido en una sesión.',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: heroTitleSize,
                                height: 0.96,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                            const SizedBox(height: 12),
                            Text(
                              'Responde con naturalidad. No hace falta explicar demasiado: me basta con señales cortas para construir algo que encaje.',
                              style: TextStyle(
                                color: Color(0xFFF5F4F0),
                                height: 1.45,
                                fontSize: heroBodySize,
                              ),
                            ),
                            const SizedBox(height: 18),
                            if (isCompactLayout)
                              SingleChildScrollView(
                                scrollDirection: Axis.horizontal,
                                child: Row(
                                  children: [
                                    EditorialStatPill(
                                      label: 'PROGRESO',
                                      value: progressText,
                                      icon: Icons.track_changes_outlined,
                                    ),
                                    const SizedBox(width: 10),
                                    EditorialStatPill(
                                      label: 'ENTORNO',
                                      value: environmentStatusText,
                                      icon: Icons.hearing_outlined,
                                    ),
                                    const SizedBox(width: 10),
                                    EditorialStatPill(
                                      label: 'APRENDIZAJE',
                                      value: explorationPreference == 'familiar'
                                          ? 'Me apoyo en memoria'
                                          : explorationPreference == 'descubrir'
                                          ? 'Abro el radar'
                                          : 'Modo equilibrado',
                                      icon: Icons.psychology_alt_outlined,
                                    ),
                                  ],
                                ),
                              )
                            else
                              Wrap(
                                spacing: 10,
                                runSpacing: 10,
                                children: [
                                  EditorialStatPill(
                                    label: 'PROGRESO',
                                    value: progressText,
                                    icon: Icons.track_changes_outlined,
                                  ),
                                  EditorialStatPill(
                                    label: 'ENTORNO',
                                    value: environmentStatusText,
                                    icon: Icons.hearing_outlined,
                                  ),
                                  EditorialStatPill(
                                    label: 'APRENDIZAJE',
                                    value: explorationPreference == 'familiar'
                                        ? 'Me apoyo en memoria'
                                        : explorationPreference == 'descubrir'
                                        ? 'Abro el radar'
                                        : 'Modo equilibrado',
                                    icon: Icons.psychology_alt_outlined,
                                  ),
                                ],
                              ),
                            const SizedBox(height: 18),
                            Row(
                              children: [
                                Expanded(
                                  child: ClipRRect(
                                    borderRadius: BorderRadius.circular(999),
                                    child: LinearProgressIndicator(
                                      minHeight: 10,
                                      value: progressValue,
                                      backgroundColor: Colors.white.withValues(
                                        alpha: 0.16,
                                      ),
                                      valueColor:
                                          const AlwaysStoppedAnimation<Color>(
                                            Color(0xFFF8E7D5),
                                          ),
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Text(
                                  _conversationCompleted
                                      ? 'Listo'
                                      : '${answeredSteps.clamp(0, 10)}/10',
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            SizedBox(height: isCompactLayout ? 10 : 14),
            Expanded(
              child: Container(
                width: double.infinity,
                decoration: const BoxDecoration(
                  color: Color(0xFFFFFCF8),
                  borderRadius: BorderRadius.vertical(top: Radius.circular(34)),
                ),
                child: ListView(
                  controller: _scrollController,
                  padding: const EdgeInsets.fromLTRB(16, 20, 16, 24),
                  children: [
                    if (!_conversationCompleted) ...[
                      StaggeredReveal(
                        order: 0,
                        child: EditorialPanel(
                          radius: 28,
                          padding: const EdgeInsets.all(18),
                          accentColor: const Color(0xFF1E4B43),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const EditorialSectionHeader(
                                eyebrow: 'CONVERSACION',
                                title: 'Una lectura breve antes de decidir.',
                                subtitle:
                                    'Cada respuesta empuja la sesión hacia un tono, una energía y un tipo de acompañamiento distinto.',
                              ),
                              const SizedBox(height: 14),
                              Wrap(
                                spacing: 10,
                                runSpacing: 10,
                                children: [
                                  _summaryChip(
                                    'Cómo vienes',
                                    _emotionAnswer.isEmpty
                                        ? 'Pendiente'
                                        : _emotionAnswer,
                                    Icons.favorite_outline,
                                  ),
                                  _summaryChip(
                                    'Qué buscas',
                                    _goalAnswer.isEmpty
                                        ? 'Pendiente'
                                        : _goalAnswer,
                                    Icons.track_changes_outlined,
                                  ),
                                  _summaryChip(
                                    'Entorno',
                                    _environmentMeasured
                                        ? _environmentUsageBadge
                                        : 'Sin medir',
                                    Icons.hearing_outlined,
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 14),
                    ],
                    ..._messages.expand(
                      (message) => [
                        _chatBubble(message),
                        const SizedBox(height: 10),
                      ],
                    ),
                    if (_conversationCompleted)
                      StaggeredReveal(
                        order: 1,
                        child: Padding(
                          padding: const EdgeInsets.only(bottom: 10),
                          child: EditorialPanel(
                            radius: 28,
                            padding: const EdgeInsets.all(18),
                            accentColor: const Color(0xFFC8845A),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const EditorialSectionHeader(
                                  eyebrow: 'RESUMEN',
                                  title: 'Todo listo antes de generar.',
                                  subtitle:
                                      'Una lectura visual de lo que has compartido antes de pasar a la recomendación final.',
                                ),
                                const SizedBox(height: 14),
                                Wrap(
                                  spacing: 10,
                                  runSpacing: 10,
                                  children: [
                                  _summaryChip(
                                    'Cómo llegas',
                                    _emotionAnswer,
                                    Icons.favorite_outline,
                                  ),
                                  _summaryChip(
                                    'Necesitas',
                                    _goalAnswer,
                                    Icons.track_changes_outlined,
                                  ),
                                  _summaryChip(
                                    'Energía',
                                    _energyAnswer,
                                    Icons.bolt_outlined,
                                  ),
                                  _summaryChip(
                                    'Tensión',
                                    _stressAnswer,
                                    Icons.psychology_alt_outlined,
                                  ),
                                  _summaryChip(
                                    'Voz',
                                    _voiceAnswer,
                                    Icons.mic_none_outlined,
                                  ),
                                  _summaryChip(
                                    'Intensidad',
                                    _intensityAnswer,
                                    Icons.graphic_eq_outlined,
                                  ),
                                  _summaryChip(
                                    'Exploración',
                                    _explorationAnswer,
                                    Icons.explore_outlined,
                                  ),
                                  _summaryChip(
                                    'Catálogo',
                                    _popularityAnswer,
                                    Icons.auto_awesome_outlined,
                                  ),
                                  _summaryChip(
                                    'Duración',
                                    _durationAnswer,
                                    Icons.schedule_outlined,
                                  ),
                                  _summaryChip(
                                    'Cómo te gustaría acabar',
                                    _desiredOutcomeAnswer,
                                    Icons.flag_outlined,
                                  ),
                                  _summaryChip(
                                    'Entorno',
                                    _environmentSummaryText,
                                    Icons.hearing_outlined,
                                  ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    if (_hasPendingQuestion && !_conversationCompleted)
                      Container(
                        width: double.infinity,
                        margin: const EdgeInsets.only(bottom: 10),
                        padding: const EdgeInsets.all(18),
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(24),
                          border: Border.all(color: const Color(0xFFE0B585)),
                          color: const Color(0xFFFFF2E3),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Se ha quedado una pregunta a medias',
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              _pendingQuestionLabel ?? 'Retomar conversación',
                              style: const TextStyle(height: 1.35),
                            ),
                            const SizedBox(height: 12),
                            FilledButton.icon(
                              onPressed: _asking ? null : _askCurrentStep,
                              icon: const Icon(Icons.refresh),
                              label: const Text('Retomar pregunta'),
                            ),
                          ],
                        ),
                      ),
                    const SizedBox(height: 12),
                  ],
                ),
              ),
            ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _ChatMessage {
  final String text;
  final bool isUser;

  const _ChatMessage({required this.text, required this.isUser});
}
