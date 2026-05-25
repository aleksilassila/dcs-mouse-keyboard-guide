# So you want to play DCS with keyboard and mouse? No problem.

Contrary to popular belief, keyboard and mouse controls in DCS can be both enjoyable and competitive with hotas setups when done right. This repository aims to explain new players where keyboard and mouse fall short of hotas and how to compensate for those shortcomings. It will also explain how my generic DCS FreePIE script works, why it is done this way and how to use the script.

If you just want to try it out and get flying, see [TLDR](#tldr-f-16-and-fa-18). If you want to understand how to \_, read on.

## FAQ

**How competitive is it with HOTAS?** Very competitive for fixed wing aircraft. By the time you are ready to start playing multiplayer, you should be able to do 90%-110% of what a HOTAS player can do. I consider helicopters playable but less enjoyable and maybe 80% as competitive as HOTAS.

...When it comes to flying and PVP, of course. Keyboard and mouse will never be as immersive as having a physical stick if you're aiming for realism.

**What hardware do I need?** Mouse and keyboard to get started. I wouldn't play without head tracking also, for this you need a webcam or a phone.

**What software do I need?** [FreePIE](https://andersmalmgren.github.io/FreePIE/), vJoy and [Opentrack](https://github.com/opentrack/opentrack) for head tracking.

<details>

<summary>What do these programs do? (click to expand)</summary>

FreePIE is a program that allows you to create custom scripts to map your input devices to virtual joysticks and other output devices. In this case, we will use it to map our keyboard and mouse inputs to a virtual joystick that DCS can recognize.

vJoy is a virtual joystick driver that creates virtual joystick devices on your computer. In other words, it acts as if you had a physical joystick connected to your computer that will show up in DCS. You can control the virtual stick programmatically using FreePIE.

</details>

**Do I need to know how to program?** Not really, if you want to just use the script. If you want to customize it, yes or just ask AI to modify it.

## TLDR (F-16 and FA-18)

Script can be found [here](DCS.v1.py). To use it, install FreePIE and vJoy, then open the script in FreePIE and run it.

- When you start it, no module is selected. To select F16 module (I use it for both F-16 and FA-18), press K+5. K+number allows you to configure different behavior for different aircraft and helicopters, and switch between them on the fly.

- You have 4+1 layers. Keys 1-F are layered keys that change behavior based on which of the Z-V layer keys are held. The default layer contains axis controls like throttle, pedal. You need ~128 virtual buttons for your vJoy because the layered keys map to virtual joystick buttons. You need to unbind all the layered keys from DCS and when binding them, bind them under the virtual joystick's buttons, not as keyboard buttons.

## Mouse vs Joystick

To understand why mouse is a bad joystick by default, let's first spell out their differences.

## What controls does a typical HOTAS have?

Skip this section if you are already familiar with typical HOTAS controls.

## What modules can you play with K&M?

I've tried the following:

- F-16: Works without issues.
- F/A-18: Works without issues.
- A-4E-C: Sure, although the slight inaccuracy of virtual joystick placement puts you at a disadvantage compared to HOTAS players.

- UH-60L: Very enjoyable
- OH-6A: Pretty rough, but playable and learnable.
- UH-1H: Pretty rough, but playable and learnable.

In general: fixed wing aircraft that have fly-by-wire controls work very well and don't put you at a disadvantage compared to HOTAS players. Older models have a bit steeper learning curve and require more muscle memory and precision so that you don't stall in turns. Helicopters are playable but the older models that lack all flight assistance will require quite a lot of dedication. You'll also need to bind the pedals to your mouse wheel for sufficient yaw control.

## Keyboard layers

When it comes to keybinds, K&M users are in luck. You will never have the issue of your hotas not mapping to your aircraft controls one to one. Your keyboard will never run out of buttons to bind, since you can multiply the number of available keys with layers and modifiers.

I use 4+1 layers for my keybinds in addition to shift and ctrl used as modifiers occasionally. This means the keys 1-4, Q-R and A-F behave differently depending on which of the keys Z-V is held down (I have dubbed the 5th layer (when nothing is held) as the _control layer_). In total this gives me 5 x 3 x 4 = 60 buttons that I can press without moving my left hand from the WASD position in addition to couple other non layered keys. Not too shabby.

DCS itself has partial support for layers, but it lacked some logic that I wanted to program in (such as hold to enable layer iirc), so the layered keys actually map to the virtual joystick's buttons 0-115 (see [what controls does a typical HOTAS have?](#what-controls-does-a-typical-hotas-have)). To map keys, you need to a) unbind keys 1-V from everything in DCS and b) when binding layered keys, bind them under the virtual joystick's buttons by pressing the desired key. Furthermore, the control layer contains axis bindings such as throttle and pedals that you can't rebind without modifying the script, but the rest of the layered keys are free to bind as you wish.

The keybinds are not complete and contain only the bare necessities to fly and fight. You might want to bind more of the buttons.

### What makes a good keybind layout?

I designed my layout with the following in mind:

- Must be able to press all aircraft HOTAS keys without moving left hand from WASD position
- Must have enough keys to bind all HOTAS buttons (layers!)
- Different layers can't have keys that need to be pressed at the same time
- Must be intuitive to use and remember

## Script layer topology

The script has 3 layers of logic as pictured below:

```
.
├── Top level "layers" are the module layers. Each layer has different mouse curves and behavior
├── UH-60L (K+1)
├── UH-1H (K+3)
├── F-16/FA-18 (K+5)
│   ├── "Freelook" mode (Mouse 5)
│   │   └── in this mode K&M is detached from controls, mouse clickable cockpit is enabled
│   └── Control mode (GRAVE key, next to 1 key)
│       ├── This is the default control mode, mouse commands pitch, roll
│       ├── Pedal control mode (R, GRAVE to exit to default control mode)
│       │   └── Here your mouse x controls your pedals, mouse 4 trims your pedals to center
│       └── Z-V layers (hold layer key to enable)
│           └── Hold to access layered keybinds
└── To get to pedal control mode of F-16, you'd start the script,
    then enable F-16 layer by pressing K+5.
    Now you are in F-16 freelook mode, nothing happens when you move your mouse or press buttons.
    You press GRAVE to go to control mode. Now you can control pitch and roll with your mouse.
    You press R to go to pedal control mode, now your mouse x controls your pedals.
    To go back to control mode, you press GRAVE again.
```

## F-16 (wip)

**Mouse keybinds**

- Mouse 1: gun
- Mouse 2: enable btn (held)
- Mouse wheel: zoom, press toggles between 2 zoom levels
- Mouse 4: hold to trim pitch to center, or trim pedals to center if in pedal control mode
- Mouse 5: enter freelook mode (disable all keybinds, detach mouse from joystick, enable clickable cockpit)

**Mouse curves and behavior**

- Pitch is always trimmed, in other words when you don't move your mouse, the virtual joystick's pitch will stay where you left it.
- When Mouse 4 is held, small constant rate and linear rates are applied to help you center the pitch perfectly.

- Roll is always trimmed to center, shift + A/D and shift + F can be used to trim the roll or reset the trim to center.
- Small constant rate and medium linear rate center the roll to trim location when mouse not moved.

**Keyboard keybinds**

![F-16 keybinds](assets/f16.png)

The rest of the keyboard uses the default DCS keybinds.

## FA-18 (more wip)

Mouse functions the same as F-16, mouse 2 is not bound currently

![FA-18 keybinds](assets/fa18.png)

## How to adjust mouse sensitivity and curves

## Helicopter control tips

- Bind pedals to mouse wheel
- Having a button in your mouse that doubles your dpi when held helps. This way you can have lower sensitivity for precision when hovering and higher sensitivity for forward flight.
- Helicopters that don't have fly-by-wire where you need to always hold some amount of roll will require you to enable continuous trim for both pitch and roll as opposed to just pitch.

## Clips

Some clips that demonstrate mouse controls in action:

https://github.com/user-attachments/assets/d8cfc1b6-5361-40e1-9aa1-a54ff2a8993d

https://github.com/user-attachments/assets/50ba377a-6bc7-4888-86d2-e259131cbe4d

https://github.com/user-attachments/assets/9725a4e2-3b2b-471a-a2ff-d3ec70427224

https://github.com/user-attachments/assets/2a6d1d8a-7f4f-4601-a249-5581a641ccf1

## Notices

Keybind diagrams were created using [keyboard shortcut map maker](https://archie-adams.github.io/keyboard-shortcut-map-maker/).

No AI was used to write this guide. Early versions of the script were AI generated.
