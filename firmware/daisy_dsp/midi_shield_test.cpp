// midi_shield_test.cpp
// -----------------------------------------------------------------------------
// TEST MINIMO DE MIDI (de-risking). SOLO MIDI: sin audio, sin SPI, sin ADSR.
// Objetivo unico: verificar que el Keystep MK2 envia y que el MIDI shield (6N138)
// pasa correctamente la senal al Daisy por USART1 (D14).
//
// Este NO es el firmware del instrumento; es una prueba de aislamiento. Para
// volver al firmware de S8, recompila SintetizadorEspacioLatente.cpp.
//
// Indicadores (dos, para poder diagnosticar con o sin PC):
//  - LED del Daisy:
//      * 3 parpadeos al arrancar  -> el firmware de test esta corriendo.
//      * encendido mientras haya alguna tecla pulsada (Note On/Off).
//  - USB serie (115200):
//      * imprime cada evento MIDI recibido (nota, velocity, canal, CC, pitch).
//      * un "latido" cada 2 s con el total de eventos, para distinguir
//        "firmware vivo pero sin MIDI" de "firmware muerto".
//
// Lectura del resultado:
//  - Pulsas tecla -> LED se enciende y sale "# NOTE_ON ..."  => la cadena
//    Keystep -> shield -> D14 FUNCIONA.
//  - Solo ves el latido y nada al pulsar => NO llega MIDI: revisa 5V del shield,
//    el switch ON/OFF, y el cable (Keystep MIDI OUT -> shield IN).
//
// Cableado (igual que S8):
//   shield RX (pin 0)  -> Daisy D14 (USART1 RX, PB7)
//   shield GND         -> Daisy GND (comun)
//   shield 5V          -> 5V reales (fuente de laboratorio), GND comun
//   Keystep MIDI OUT   -> shield IN ;  switch del shield en ON
// -----------------------------------------------------------------------------

#include "daisy_seed.h"

using namespace daisy;

DaisySeed       hw;
MidiUartHandler midi;

static int held = 0;   // teclas pulsadas actualmente (para el LED)

static void midi_init()
{
    MidiUartHandler::Config c;
    c.transport_config.periph = UartHandler::Config::Peripheral::USART_1;
    c.transport_config.rx     = {DSY_GPIOB, 7};  // D14
    c.transport_config.tx     = {DSY_GPIOB, 6};  // D13
    midi.Init(c);
    midi.StartReceive();
}

int main(void)
{
    hw.Init();
    hw.StartLog(false);   // no espera al PC: arranca aunque no haya serie abierto
    midi_init();

    // 3 parpadeos: senal visible de que el firmware de test esta corriendo.
    for(int i = 0; i < 3; ++i)
    {
        hw.SetLed(true);  System::Delay(120);
        hw.SetLed(false); System::Delay(120);
    }

    hw.PrintLine("=== MIDI SHIELD TEST (solo MIDI, sin audio/SPI) ===");
    hw.PrintLine("Pulsa teclas en el Keystep. LED encendido = tecla pulsada.");

    uint32_t last_beat = System::GetNow();
    uint32_t n_events  = 0;

    while(true)
    {
        midi.Listen();
        while(midi.HasEvents())
        {
            MidiEvent m = midi.PopEvent();
            n_events++;
            switch(m.type)
            {
                case NoteOn:
                {
                    NoteOnEvent e = m.AsNoteOn();
                    if(e.velocity > 0)
                    {
                        held++;
                        hw.PrintLine("# NOTE_ON  ch=%d note=%d vel=%d held=%d",
                                     e.channel, (int)e.note, (int)e.velocity, held);
                    }
                    else   // Note On con velocity 0 = Note Off (running status)
                    {
                        if(held > 0) held--;
                        hw.PrintLine("# NOTE_OFF ch=%d note=%d (vel0) held=%d",
                                     e.channel, (int)e.note, held);
                    }
                }
                break;
                case NoteOff:
                {
                    NoteOffEvent e = m.AsNoteOff();
                    if(held > 0) held--;
                    hw.PrintLine("# NOTE_OFF ch=%d note=%d held=%d",
                                 e.channel, (int)e.note, held);
                }
                break;
                case ControlChange:
                {
                    ControlChangeEvent e = m.AsControlChange();
                    hw.PrintLine("# CC        ch=%d num=%d val=%d",
                                 e.channel, (int)e.control_number, (int)e.value);
                }
                break;
                case PitchBend:
                {
                    PitchBendEvent e = m.AsPitchBend();
                    hw.PrintLine("# PITCHBEND ch=%d val=%d", e.channel, (int)e.value);
                }
                break;
                default:
                    hw.PrintLine("# EVENT     type=%d", (int)m.type);
                    break;
            }
        }

        // LED = hay alguna tecla pulsada.
        hw.SetLed(held > 0);

        // Latido cada 2 s: prueba de vida aunque no llegue MIDI.
        if(System::GetNow() - last_beat >= 2000)
        {
            hw.PrintLine("# vivo, esperando MIDI... eventos_totales=%u",
                         (unsigned)n_events);
            last_beat = System::GetNow();
        }

        System::Delay(1);
    }
}
