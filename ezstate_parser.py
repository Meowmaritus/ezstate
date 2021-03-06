# -*- coding: utf-8 -*-
"""
@author: grimrhapsody
"""

from struct import unpack


REGISTERS = [''] * 8


def reset_registers():
    global REGISTERS
    REGISTERS = [''] * 8


marker_lookup = {
    '91': '<=',
    '92': '>=',
    '93': '<',
    '94': '>',
    '95': '==',
    '96': '!=',
}

function_lookup = {
    # Not all of these are confirmed. Feel free to study the code and present evidence.
    # Note that these indices are completely different to the on/off command IDs.
    0: 'GetWhetherEnemiesAreNearby',
    1: 'GetDistanceToPlayer',
    2: 'HasTalkEnded',
    3: 'CheckSelfDeath',
    4: 'IsPlayerTalkingToMe',
    5: 'IsAttackedBySomeone',
    6: 'GetMyHp', # from 0 to 100.
    7: 'GetDistanceFromEnemy',
    8: 'GetRelativeAngleBetweenPlayerAndSelf',
    9: 'IsPlayerAttacking',
    10: 'GetRelativeAngleBetweenSelfAndPlayer',
    11: 'IsTalkInProgress',
    12: 'GetTalkInterruptReason',
    13: 'GetShopCondition',
    14: 'GetOneLineHelpStatus',
    15: 'GetEventStatus',
    16: 'IsEquipmentIDObtained', # (equipment_type, item_id)
    17: 'IsEquipmentIDEquipped', # (equipment_type, equipment_param_id)
    18: 'IsFightingAlone',
    19: 'IsClientPlayer',
    20: 'IsCampMenuOpen',
    21: 'IsGenericDialogOpen',
    22: 'GetGenericDialogButtonResult', # 0 = Cancel button, 1 = Yes, 2 = No
    23: 'GetTalkListEntryResult',
    24: 'IsMoviePlaying',
    25: 'IsMenuOpen',
    26: 'IsCharacterDisabled',
    27: 'IsPlayerDead',
    28: 'DidYouDoSomethingInTheMenu',
    29: 'GetStatus',
    30: 'IsPlayerMovingACertainDistance',
    31: 'IsTalkingToSomeoneElse',
    32: 'HasDisableTalkPeriodElapsed',
    33: 'HasPlayerBeenAttacked',
    34: 'GetPlayerYDistance',
    35: 'GetPlayerChrType',
    36: 'CanIGoToNextTalkBlock',
    37: 'CompareBonfireState',
    38: 'CompareBonfireLevel',
    39: 'CompareParentBonfire',
    40: 'BonfireRegistration0',
    41: 'BonfireRegistration1',
    42: 'BonfireRegistration2',
    43: 'BonfireRegistration3',
    44: 'BonfireRegistration4',
    45: 'ComparePlayerStatus',
    46: 'RelativeAngleBetweenTwoPlayers_SpecifyAxis',
    47: 'ComparePlayerInventoryNumber',
    48: 'IsPlayerCurrentWeaponDamaged',
    49: 'ComparePlayerAcquittalPrice',
    50: 'CompareRNGValue',
    51: 'WasWarpMenuDestinationSelected',
    52: 'IsMultiplayerInProgress',
    53: 'IsTalkExclusiveMenuOpen',
    54: 'IsRankingMenuOpen',
    55: 'GetPlayerRemainingHP',
    56: 'CheckActionButtonArea',
    57: 'CheckSpecificPersonTalkHasEnded',
    58: 'CheckSpecificPersonGenericDialogIsOpen',
    59: 'CheckSpecificPersonMenuIsOpen',
    60: 'DoesSelfHaveSpEffect',
    61: 'DoesPlayerHaveSpEffect',
    62: 'GetValueFromNumberSelectDialog',
    63: 'GetWorkValue',
    64: 'GetEventFlagValue',
    65: 'GetCurrentStateElapsedFrames',
    66: 'GetCurrentStateElapsedTime',
    67: 'GetPlayerStatus',
    68: 'GetLevelUpSoulCost',
    69: 'GetWhetherChrTurnAnimHasEnded',
    70: 'GetWhetherChrEventAnimHasEnded',
    71: 'GetItemHeldNumLimit',
}


def ezparse(input_line, full_brackets=False):
    """ input_line can be a bytes object, or a list of hex byte strings. """
    if isinstance(input_line, bytes):
        input_line = [input_line[i:i+1].hex() for i in range(len(input_line))]

    global REGISTERS

    output_line = []
    offset = 0

    while offset < len(input_line):

        byte = input_line[offset]
        offset += 1

        if '3f' <= byte <= '7f':
            # Interpret byte as an integer offset by +64 (so can represent integers -1 to 63). [82] needed otherwise.
            output_line.append(str(int(byte, 16) - 64))

        else:

            if byte == 'a5':
                # Read a null-terminated UTF-16LE string.
                string = ''
                hex_chr = bytearray.fromhex(''.join(input_line[offset:offset+2]))
                offset += 2
                while hex_chr != b'\x00\x00':
                    string += hex_chr.decode('utf-16le')
                    hex_chr = bytearray.fromhex(''.join(input_line[offset:offset + 2]))
                    offset += 2
                output_line.append(string)

            elif byte == '80':
                # Next four bytes form a single-precision float.
                float_value = unpack('<f', bytearray.fromhex(''.join(input_line[offset:offset + 4])))[0]
                offset += 4
                output_line.append(str(float_value))

            elif byte == '81':
                # Next eight bytes form a double-precision float.
                double_value = unpack('<d', bytearray.fromhex(''.join(input_line[offset:offset + 8])))[0]
                offset += 8
                output_line.append(str(double_value))

            elif byte == '82':
                # Next four bytes form an integer.
                integer = unpack('<i', bytearray.fromhex(''.join(input_line[offset:offset + 4])))[0]
                offset += 4
                output_line.append(str(integer))

            # I haven't seen byte '83' yet but it's safe to say it will indicate a data type - maybe a string.

            elif byte == '84':
                # Previous integer is a function index with no arguments.
                function_index = int(output_line[-1])
                function_name = function_lookup.get(function_index, 'method_{}'.format(function_index))
                output_line[-1] = function_name + '()'

            elif byte == '85':
                # Previous two values represent a function index and one argument (in that order).
                function_index = int(output_line[-2])
                function_name = function_lookup.get(function_index, 'method_{}'.format(function_index))
                output_line[-2] = function_name + '({})'.format(output_line[-1])
                output_line.pop()   # function and argument have been combined

            elif byte == '86':
                # Previous three values represent a function index and two arguments (in that order).
                function_index = int(output_line[-3])
                function_name = function_lookup.get(function_index, 'method_{}'.format(function_index))
                output_line[-3] = function_name + '({}, {})'.format(*output_line[-2:])
                output_line.pop()   # function and arguments have been combined
                output_line.pop()

            elif byte == '87':
                # Previous four values represent a function index and three arguments (in that order).
                function_index = int(output_line[-4])
                function_name = function_lookup.get(function_index, 'method_{}'.format(function_index))
                output_line[-4] = function_name + '({}, {}, {})'.format(*output_line[-3:])
                output_line.pop()   # function and arguments have been combined
                output_line.pop()
                output_line.pop()

            # I assume bytes 88-8b mark functions that take 5/6/7 arguments but haven't encountered them yet to confirm.

            # I think 8c is a simple binary operation, probably addition. That means 8d, 8e, 8f could be subtraction,
            # multiplication, and division. Not sure about 90.

            elif '91' <= byte <= '96':
                # Applies comparison operator to the last two values (left and right, respectively).
                comparison_operator = marker_lookup[byte]
                output_line[-2] = '({} {} {})'.format(output_line[-2], comparison_operator, output_line[-1])
                output_line.pop()

            elif byte == '98':
                # Applies AND operation to the last two values.
                if full_brackets:
                    output_line[-2] = '({}) and ({})'.format(output_line[-2], output_line[-1])
                else:
                    output_line[-2] = '{} and {}'.format(output_line[-2], output_line[-1])
                output_line.pop()

            elif byte == '99':
                # Applies OR operation to the last two values.
                if full_brackets:
                    output_line[-2] = '({}) or ({})'.format(output_line[-2], output_line[-1])
                else:
                    output_line[-2] = '{} or {}'.format(output_line[-2], output_line[-1])
                output_line.pop()

            elif byte == 'a1':
                # End of line. Not printed. Note that it is NOT responsible for registering the state change conditions,
                # as it appears in command argument data as well. It's strictly an end line marker. Also note that it
                # can appear elsewhere in the code, such as in the value of an integer or float, and it is therefore NOT
                # safe to blindly parse the packed data based solely on this byte.
                pass

            elif byte == 'a6':
                # My leading hypothesis for this byte is that it forces the command to continue even when the previous
                # value is false (0), which would normally stop the condition line from continuing. I have left this
                # byte out of the normal display mode, but you can enable it (and b7) with show_continuation=True.
                output_line[-1] += '^'
                pass

            elif 'a7' <= byte <= 'ae':
                # Save previous value to register.
                REGISTERS[int(byte, 16) - 167] = output_line[-1]

            elif 'af' <= byte <= 'b6':
                # Load value from register. The ampersand indicates that this value has been computed earlier in the
                # state conditions, which ensures that values do not change during a single evaluation of the conditions
                # for each potential state change.
                output_line.append('&'+REGISTERS[int(byte, 16) - 175])

            elif byte == 'b7':
                # My leading hypothesis for this byte is that it stops the current line from continuing evaluation if
                # the previous value is false (0). It usually occurs later in the state because early conditions often
                # *must* finish evaluating to save computed values for later loading. It also occurs in situations like
                # "1 and (2 or 3 or 4)", when the AND command does not occur until the end of the command.
                #
                # Obviously, this hypothesis isn't fully consistent with my hypothesis about 'a6', which assumed that
                # values of 0 can halt a command. It's possible that the developers occasionally used these continuation
                # instructions superfluously. Or I could be wrong about one or both of them.
                output_line[-1] += '!'

            else:
                marker = marker_lookup.get(byte, '[{}]'.format(byte))
                output_line.append(marker)

    return ' '.join(output_line)
