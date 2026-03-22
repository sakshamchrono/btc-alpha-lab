import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:todo_app/main.dart'; // Assuming your main file is in lib/main.dart

void main() {
  group('TodoApp Tests', () {
    testWidgets('App initializes and displays correctly', (WidgetTester tester) async {
      // Build our app and trigger a frame.
      await tester.pumpWidget(const MyApp());

      // Verify that the title is displayed
      expect(find.text('To-Do List'), findsOneWidget);

      // Verify that the input field is present
      expect(find.byType(TextField), findsOneWidget);

      // Verify that the add button is present
      expect(find.byIcon(Icons.add), findsOneWidget);
    });

    testWidgets('Add a new todo item', (WidgetTester tester) async {
      await tester.pumpWidget(const MyApp());

      // Enter text into the input field
      await tester.enterText(find.byType(TextField), 'Buy groceries');

      // Tap the add button
      await tester.tap(find.byIcon(Icons.add));
      await tester.pump(); // Rebuild the widget after the state has changed

      // Verify that the new todo item is displayed
      expect(find.text('Buy groceries'), findsOneWidget);
      expect(find.textContaining('Created:'), findsOneWidget);
    });

    testWidgets('Toggle todo item completion', (WidgetTester tester) async {
      await tester.pumpWidget(const MyApp());

      // Add a todo item
      await tester.enterText(find.byType(TextField), 'Walk the dog');
      await tester.tap(find.byIcon(Icons.add));
      await tester.pump();

      // Find the checkbox and tap it
      final checkboxFinder = find.byType(Checkbox).first;
      await tester.tap(checkboxFinder);
      await tester.pump();

      // Verify that the text has a line-through decoration
      final textWidget = tester.widget<Text>(find.text('Walk the dog'));
      expect((textWidget.style?.decoration ?? TextDecoration.none), TextDecoration.lineThrough);
    });

    testWidgets('Delete a todo item', (WidgetTester tester) async {
      await tester.pumpWidget(const MyApp());

      // Add a todo item
      await tester.enterText(find.byType(TextField), 'Clean the house');
      await tester.tap(find.byIcon(Icons.add));
      await tester.pump();

      // Find and tap the delete button
      await tester.tap(find.byIcon(Icons.delete).first);
      await tester.pump();

      // Verify that the todo item is no longer displayed
      expect(find.text('Clean the house'), findsNothing);
    });
  });
}
