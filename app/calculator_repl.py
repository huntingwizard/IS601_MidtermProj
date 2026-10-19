from decimal import Decimal
from app.operations import OperationFactory
from app.calculator import Calculator
from app.exceptions import OperationError, ValidationError
from app.history import AutoSaveObserver, LoggingObserver


def calculator_repl():
    try:
        calc=Calculator()
        calc.add_observer(LoggingObserver())
        calc.add_observer(AutoSaveObserver(calc))
        operations = sorted(OperationFactory._operations)
        while True:
            try:
                inp=input("Enter command: ").lower().strip()
                if inp=="help":
                    print("\nAvailable commands:")
                    print("\nOperations:", ", ".join(operations))
                    print("  history - Show calculation history")
                    print("  clear - Clear calculation history")
                    print("  undo - Undo the last calculation")
                    print("  redo - Redo the last undone calculation")
                    print("  save - Save calculation history to file")
                    print("  load - Load calculation history from file")
                    print("  exit - Exit the calculator")
                elif inp=="exit":
                    print("C U LATER")
                    break
                elif inp == "history":
                    entries = calc.show_history()
                    print("No calculations in history" if not entries else
                        "\n".join(f"{i}. {e}" for i, e in enumerate(entries, 1)))
                elif inp == "clear":
                    calc.clear_history(); print("History cleared")
                elif inp == "undo":
                    print("Operation undone" if calc.undo() else "Nothing to undo")
                elif inp == "redo":
                    print("Operation redone" if calc.redo() else "Nothing to redo")
                elif inp in ("save", "load"):
                    try:
                        calc.save_history() if inp == "save" else calc.load_history()
                        print(f"History {inp}d successfully")
                    except OperationError as e:
                        print(f"Error: {e}")
                elif inp in ["add", "subtract", "multiply", "divide", "power", "root", "modulus", "int_divide", "percent", "abs_diff"]:
                    try:
                        print("\n enter your 2 number inputs")
                        a=input("First Input ")
                        b=input("Second input ")
                        operation = OperationFactory.create_operation(inp)
                        calc.set_operation(operation)

                        calc.perform_operation(a, b)
                        print(f"\nResult: {calc.last_calculation.format_result(calc.config.precision)}")
                    
                    except (ValidationError, OperationError) as e:
                    # Handle known exceptions related to validation or operation errors
                        print(f"Error: {e}")
                    except Exception as e:
                        print(f"Unexpcted error: {e}")
                else:
                    print(f"Unknown command: '{inp}'. Type 'help' for available commands.")
            except KeyboardInterrupt:
                # Handle Ctrl+C interruption gracefully
                print("\nOperation cancelled")
                continue
            except EOFError:
                # Handle end-of-file (e.g., Ctrl+D) gracefully
                print("\nInput terminated. Exiting...")
                break  
            except Exception as e:
                print(f"Error: {e}")  
    except Exception as e:
        print(f"Fatal error: {e}")
    return 0