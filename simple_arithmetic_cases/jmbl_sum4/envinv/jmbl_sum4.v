module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [10:0] i,
    output reg [10:0] sn
);


    always@(posedge clk) begin
        $display("i: %b, sn: %b", i,sn);
    end 
    
    always @(posedge clk) begin
        if(rst)begin
            i<=1;
            sn<=0;
        end
        else begin 
            if(i<=250)begin
                i<=i+1;
                if(i<=150)begin
                    sn<=sn+1;
                    end
                end
            else begin
                i<=i;
                sn<=sn; 
                end
        end
    end
    
    // assert property ((i<=150)||(sn==150));
endmodule