module smaller_tb();
    reg  clk = 1;
    reg  rst = 1;
    reg selector;

    wire [7:0] x;
    wire [7:0] y;
    top RTL(.clk(clk), 
            .rst(rst),
            .selector(selector),
            .x(x),
            .y(y)
    );

    // Generated internal use signals
    // reg  [31:0] _conc_pc;
    // reg  [1:0] _conc_opcode;
    // reg  [1:0] _conc_ram[0:15];


    // Generated clock pulse
    always begin
        #5 clk = ~clk;
    end

    // initial begin
    //     #0 rst= 1;
    //     #8 rst= 0;
    //     #10000 $finish; // 结束仿真
    // end

    integer i;
    initial begin
    // simulate 1000 cycles 
        for (i = 0; i < 1000; i = i + 1) begin
            selector <={1{$random}};
            // dummy_read_rf = {2{$random}};
            // dummy_rf_data = {8{$random}};
            rst <= 0;
            #10;
        end
        
        $finish; // 结束仿真
    end

    // initial
    // begin            
    //     $dumpfile("wave.vcd");        //生成的vcd文件名称
    //     $dumpvars(0, RTL);    //tb模块名称
    //     $finish; // 结束仿真
    // end 
endmodule