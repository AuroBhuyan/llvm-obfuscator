; ModuleID = '/home/aurobhuyan/llvm-obfuscator/test/input.cpp'
source_filename = "/home/aurobhuyan/llvm-obfuscator/test/input.cpp"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-pc-linux-gnu"

@secret_key = dso_local global i32 42, align 4
@.str = private unnamed_addr constant [22 x i8] c"compute(10, 5)  = %d\0A\00", align 1
@.str.1 = private unnamed_addr constant [22 x i8] c"compute(3, 9)   = %d\0A\00", align 1
@.str.2 = private unnamed_addr constant [22 x i8] c"factorial(6)    = %d\0A\00", align 1
@.str.3 = private unnamed_addr constant [22 x i8] c"Secret key      = %d\0A\00", align 1

; Function Attrs: mustprogress noinline nounwind optnone uwtable
define dso_local noundef i32 @_Z7computeii(i32 noundef %0, i32 noundef %1) #0 {
  %3 = alloca i32, align 4
  %4 = alloca i32, align 4
  %5 = alloca i32, align 4
  store i32 %0, i32* %4, align 4
  store i32 %1, i32* %5, align 4
  %6 = load i32, i32* %4, align 4
  %7 = load i32, i32* %5, align 4
  %8 = icmp sgt i32 %6, %7
  br i1 %8, label %9, label %15

9:                                                ; preds = %2
  %10 = load i32, i32* %4, align 4
  %11 = load i32, i32* %5, align 4
  %12 = mul nsw i32 %10, %11
  %13 = load i32, i32* @secret_key, align 4
  %14 = add nsw i32 %12, %13
  store i32 %14, i32* %3, align 4
  br label %21

15:                                               ; preds = %2
  %16 = load i32, i32* %4, align 4
  %17 = load i32, i32* %5, align 4
  %18 = add nsw i32 %16, %17
  %19 = load i32, i32* @secret_key, align 4
  %20 = sub nsw i32 %18, %19
  store i32 %20, i32* %3, align 4
  br label %21

21:                                               ; preds = %15, %9
  %22 = load i32, i32* %3, align 4
  ret i32 %22
}

; Function Attrs: mustprogress noinline optnone uwtable
define dso_local noundef i32 @_Z9factoriali(i32 noundef %0) #1 {
  %2 = alloca i32, align 4
  %3 = alloca i32, align 4
  store i32 %0, i32* %3, align 4
  %4 = load i32, i32* %3, align 4
  %5 = icmp sle i32 %4, 1
  br i1 %5, label %6, label %7

6:                                                ; preds = %1
  store i32 1, i32* %2, align 4
  br label %13

7:                                                ; preds = %1
  %8 = load i32, i32* %3, align 4
  %9 = load i32, i32* %3, align 4
  %10 = sub nsw i32 %9, 1
  %11 = call noundef i32 @_Z9factoriali(i32 noundef %10)
  %12 = mul nsw i32 %8, %11
  store i32 %12, i32* %2, align 4
  br label %13

13:                                               ; preds = %7, %6
  %14 = load i32, i32* %2, align 4
  ret i32 %14
}

; Function Attrs: mustprogress noinline norecurse optnone uwtable
define dso_local noundef i32 @main() #2 {
  %1 = alloca i32, align 4
  store i32 0, i32* %1, align 4
  %2 = call noundef i32 @_Z7computeii(i32 noundef 10, i32 noundef 5)
  %3 = call i32 (i8*, ...) @printf(i8* noundef getelementptr inbounds ([22 x i8], [22 x i8]* @.str, i64 0, i64 0), i32 noundef %2)
  %4 = call noundef i32 @_Z7computeii(i32 noundef 3, i32 noundef 9)
  %5 = call i32 (i8*, ...) @printf(i8* noundef getelementptr inbounds ([22 x i8], [22 x i8]* @.str.1, i64 0, i64 0), i32 noundef %4)
  %6 = call noundef i32 @_Z9factoriali(i32 noundef 6)
  %7 = call i32 (i8*, ...) @printf(i8* noundef getelementptr inbounds ([22 x i8], [22 x i8]* @.str.2, i64 0, i64 0), i32 noundef %6)
  %8 = load i32, i32* @secret_key, align 4
  %9 = call i32 (i8*, ...) @printf(i8* noundef getelementptr inbounds ([22 x i8], [22 x i8]* @.str.3, i64 0, i64 0), i32 noundef %8)
  ret i32 0
}

declare i32 @printf(i8* noundef, ...) #3

attributes #0 = { mustprogress noinline nounwind optnone uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { mustprogress noinline optnone uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #2 = { mustprogress noinline norecurse optnone uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #3 = { "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }

!llvm.ident = !{!5}

!0 = !{i32 1, !"wchar_size", i32 4}

!5 = !{!"Ubuntu clang version 14.0.0-1ubuntu1.1"}
