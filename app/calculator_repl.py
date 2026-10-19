from app.operations import OperationFactory
from app.calculator import Calculator
from app.exceptions import OperationError, ValidationError
from app.history import AutoSaveObserver, LoggingObserver
from app.colors import error, info, prompt, success, warning

def calculator_repl():
    try:
        calc=Calculator()
        calc.add_observer(LoggingObserver())
        calc.add_observer(AutoSaveObserver(calc))
        operations = sorted(OperationFactory._operations)
        print(info("Calculator started. Type 'help' for commands."))
        while True:
            try:
                inp=input(prompt("Enter command: ")).lower().strip()
                if inp=="help":
                    print(info("\nAvailable commands:"))
                    print(info("\nOperations: " + ", ".join(operations)))
                    print(info("  history - Show calculation history"))
                    print(info("  clear - Clear calculation history"))
                    print(info("  undo - Undo the last calculation"))
                    print(info("  redo - Redo the last undone calculation"))
                    print(info("  save - Save calculation history to file"))
                    print(info("  load - Load calculation history from file"))
                    print(info("  exit - Exit the calculator"))
                elif inp=="exit":
                    print(info("C U LATER"))
                    break
                elif inp == "history":
                    entries = calc.show_history()
                    if not entries:
                        print(warning("No calculations in history"))
                    else:
                        for i, e in enumerate(entries, 1):
                            print(info(f"{i}. {e}"))
                elif inp == "clear":
                    calc.clear_history()
                    print(success("History cleared"))
                elif inp == "undo":
                    print(success("Operation undone") if calc.undo() else warning("Nothing to undo"))
                elif inp == "redo":
                    print(success("Operation redone") if calc.redo() else warning("Nothing to redo"))
                elif inp in ("save", "load"):
                    try:
                        calc.save_history() if inp == "save" else calc.load_history()
                        print(success(f"History {'saved' if inp == 'save' else 'loaded'} successfully"))
                    except OperationError as e:
                        print(error(f"Error: {e}"))
                elif inp in ["add", "subtract", "multiply", "divide", "power", "root", "modulus", "int_divide", "percent", "abs_diff"]:
                    try:
                        print(info("\n enter your 2 number inputs"))
                        a=input(prompt("First Input "))
                        b=input(prompt("Second input "))
                        operation = OperationFactory.create_operation(inp)
                        calc.set_operation(operation)

                        calc.perform_operation(a, b)
                        print(success(f"\nResult: {calc.last_calculation.format_result(calc.config.precision)}"))

                    except (ValidationError, OperationError) as e:
                        # Handle known exceptions related to validation or operation errors
                        print(error(f"Error: {e}"))
                    except Exception as e:
                        print(error(f"Unexpected error: {e}"))
                else:
                    print(warning(f"Unknown command: '{inp}'. Type 'help' for available commands."))
            except KeyboardInterrupt:
                # Handle Ctrl+C interruption gracefully
                print(warning("\nOperation cancelled"))
                continue
            except EOFError:
                # Handle end-of-file (e.g., Ctrl+D) gracefully
                print(warning("\nInput terminated. Exiting..."))
                break
            except Exception as e:
                print(error(f"Error: {e}"))
    except Exception as e:
        print(error(f"Fatal error: {e}"))
    return 0